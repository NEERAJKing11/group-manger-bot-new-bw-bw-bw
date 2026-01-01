# handlers.py
import telebot
import re
import database
import config

bot = telebot.TeleBot(config.API_TOKEN)

# --- COMMANDS ---

@bot.message_handler(commands=['register'])
def handle_register(message):
    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.reply_to(message, "⚠️ Use: `/register YourName`")
            return
        name = parts[1].strip()
        status = database.register_student(message.from_user.id, name)
        bot.reply_to(message, f"✅ {status}: **{name}** added to Board Wallah List.")
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

@bot.message_handler(commands=['end_day'])
def handle_end_day(message):
    """
    Raat ko admin ye command chalayega to strikes lagengi.
    """
    # Security: Sirf admin ya owner chala sake
    if message.from_user.id not in [config.OWNER_ID]: 
        # Aap chahein to yahan group admin check bhi laga sakte hain
        pass 

    bot.reply_to(message, "⏳ Calculating final report & strikes... Please wait.")
    
    data = database.process_end_of_day_strikes()
    
    # KICK LOGIC
    for uid in data['to_kick_ids']:
        try:
            bot.kick_chat_member(config.GROUP_ID, uid)
            bot.send_message(config.GROUP_ID, f"🚫 **Banned:** User ID {uid} due to 3 Strikes.")
        except Exception as e:
            print(f"Failed to kick {uid}: {e}")

    # GENERATE REPORT
    report = "🌙 **FINAL DAILY REPORT** 🌙\n"
    report += f"📅 Date: {database.get_today_date()}\n\n"
    
    if data['present']:
        report += f"✅ **Safe (Present Today):**\n" + ", ".join(data['present']) + "\n\n"
    
    if data['absent_struck']:
        report += f"⚠️ **Absent (Strike Added):**\n" + "\n".join(data['absent_struck']) + "\n\n"
        
    if data['kicked']:
        report += f"🚫 **KICKED FROM GROUP:**\n" + "\n".join(data['kicked']) + "\n"
        
    bot.send_message(message.chat.id, report, parse_mode="Markdown")

# --- LEADERBOARD HANDLING ---

@bot.message_handler(func=lambda m: m.text and ("🏆" in m.text or "Top Results" in m.text))
def handle_quiz_result(message):
    """Leaderboard aate hi attendance lagayega"""
    
    raw_text = message.text
    # Parse Names (Regex to find 1. Name - Score)
    parsed_names = []
    lines = raw_text.split('\n')
    topper = "Unknown"
    
    for line in lines:
        match = re.search(r'\d+\.\s+(.*?)\s+[–-]', line)
        if match:
            name = match.group(1).strip()
            parsed_names.append(name)
            if line.startswith("1.") or "🥇" in line:
                topper = name

    if not parsed_names:
        bot.reply_to(message, "⚠️ Leaderboard read nahi kar paya. Format check karein.")
        return

    # Mark Attendance in DB
    present_list = database.mark_attendance(parsed_names)
    
    # Instant Reply (No Strikes yet)
    msg = f"📊 **Attendance Updated!**\n\n"
    msg += f"🥇 **Topper:** {topper}\n"
    msg += f"✅ **Matched Students ({len(present_list)}):**\n" + ", ".join(present_list)
    msg += "\n\nℹ️ *Note: Strikes will be calculated when you run /end_day command.*"
    
    bot.reply_to(message, msg, parse_mode="Markdown")
