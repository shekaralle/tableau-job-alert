import requests
import os
import re
import json
from flask import Flask

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

LOCATION = "pune"
KEYWORD = "tableau"

SEEN_FILE = "seen_jobs.json"

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen():
    with open(SEEN_FILE, "w") as f:
        json.dump(list(SEEN), f)

SEEN = load_seen()

def send(msg):
    if not BOT_TOKEN or not CHAT_ID:
        return
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg}
    )

def contains_tableau(text):
    return KEYWORD in text.lower()

def check_linkedin():
    url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    params = {
        "keywords": "tableau",
        "location": "Pune",
        "f_TPR": "r86400"
    }

    r = requests.get(url, params=params)
    ids = re.findall(r'jobPosting:(\d+)', r.text)

    for job_id in ids:
        link = f"https://www.linkedin.com/jobs/view/{job_id}"

        if link in SEEN:
            continue

        SEEN.add(link)
        save_seen()
        send(f"Tableau Job — LinkedIn\n{link}")

@app.route("/")
def scan():
    check_linkedin()
    return "OK"
