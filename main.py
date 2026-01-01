# main.py
import handlers
import time

if __name__ == "__main__":
    print("--- Board Wallah Bot Started ---")
    print("Waiting for Quiz Leaderboards...")
    try:
        handlers.bot.infinity_polling()
    except Exception as e:
        print(f"Critical Error: {e}")
        time.sleep(5)
