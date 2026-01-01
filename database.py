# database.py
from pymongo import MongoClient
import config
from datetime import datetime
import certifi

# Connect to Database
client = MongoClient(config.MONGO_URI, tlsCAFile=certifi.where())
db = client[config.DB_NAME]
users_col = db[config.COLLECTION_NAME]

def get_today_date():
    return datetime.now().strftime("%Y-%m-%d")

def register_student(user_id, name):
    """Naye student ko register karna"""
    existing = users_col.find_one({'user_id': user_id})
    if existing:
        users_col.update_one({'user_id': user_id}, {'$set': {'name': name}})
        return "Updated"
    else:
        user_data = {
            'user_id': user_id,
            'name': name,
            'strikes': 0,
            'last_present_date': None,
            'joined_date': get_today_date()
        }
        users_col.insert_one(user_data)
        return "Registered"

def mark_attendance(parsed_names):
    """List me aaye naamo ki hazri lagana"""
    today = get_today_date()
    marked_count = 0
    present_names = []

    all_students = list(users_col.find({}))
    
    for student in all_students:
        s_name = student['name']
        # Check if student name is in the parsed leaderboard names
        # (Case insensitive matching)
        if any(s_name.lower() in p_name.lower() for p_name in parsed_names):
            users_col.update_one(
                {'_id': student['_id']}, 
                {'$set': {'last_present_date': today}}
            )
            present_names.append(s_name)
            marked_count += 1
            
    return present_names

def process_end_of_day_strikes():
    """Din ke ant me absent logo ko strike dena"""
    today = get_today_date()
    all_students = list(users_col.find({}))
    
    report_data = {
        'present': [],
        'absent_struck': [],
        'kicked': [],
        'to_kick_ids': []
    }

    for student in all_students:
        last_date = student.get('last_present_date')
        
        if last_date == today:
            # Ye aaj kisi ek quiz me aaya tha - SAFE
            report_data['present'].append(student['name'])
        else:
            # Ye aaj kisi bhi quiz me nahi aaya - STRIKE
            new_strikes = student.get('strikes', 0) + 1
            users_col.update_one(
                {'_id': student['_id']},
                {'$set': {'strikes': new_strikes}}
            )
            
            if new_strikes >= 3:
                report_data['kicked'].append(f"{student['name']} (3 Strikes)")
                report_data['to_kick_ids'].append(student['user_id'])
                # Optional: Delete from DB after kick
                users_col.delete_one({'_id': student['_id']})
            else:
                report_data['absent_struck'].append(f"{student['name']} (Strikes: {new_strikes}/3)")
    
    return report_data
