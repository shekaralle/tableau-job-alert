import requests
import time
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

KEYWORDS = ["tableau"]
LOCATION = "pune"

SEEN_JOBS = set()

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    data = {
        "chat_id": CHAT_ID,
        "text": message
    }
    
    requests.post(url, data=data)

def fetch_workday_jobs():
    
    url = "https://wd5.myworkdayjobs.com/wday/cxs/wday/job"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        for job in data.get("jobPostings", []):
            
            title = job.get("title", "")
            location = job.get("locationsText", "")
            link = job.get("externalPath", "")
            
            if LOCATION.lower() in location.lower() and any(k in title.lower() for k in KEYWORDS):
                
                if link not in SEEN_JOBS:
                    
                    SEEN_JOBS.add(link)
                    
                    message = f"""
New Tableau Job!

Title: {title}
Location: {location}

https://wd5.myworkdayjobs.com{link}
"""
                    
                    send_telegram(message)
                    
    except Exception as e:
        print(e)

while True:
    
    fetch_workday_jobs()
    
    time.sleep(300)
