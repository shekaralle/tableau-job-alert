import requests
import time
import os
import threading
from flask import Flask

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

KEYWORDS = ["tableau"]
LOCATION = "pune"

SEEN_JOBS = set()

app = Flask(__name__)

@app.route('/')
def home():
    return "Job Alert Bot Running"

def send_telegram(message):
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    data = {
        "chat_id": CHAT_ID,
        "text": message
    }
    
    requests.post(url, data=data)

def job_checker():
    
    send_telegram("Job Alert Bot Started Successfully")
    
    while True:
        
        print("Checking jobs...")
        
        # test message every 10 mins
        # remove later
        # send_telegram("Bot still running")
        
        time.sleep(600)

def run_bot():
    threading.Thread(target=job_checker).start()

if __name__ == "__main__":
    
    run_bot()
    
    port = int(os.environ.get("PORT", 10000))
    
    app.run(host="0.0.0.0", port=port)
