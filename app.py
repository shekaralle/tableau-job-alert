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

# ----------------------------
# Load / Save Seen Jobs
# ----------------------------

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen():
    with open(SEEN_FILE, "w") as f:
        json.dump(list(SEEN), f)

SEEN = load_seen()

# ----------------------------
# Telegram Sender
# ----------------------------

def send(msg):
    if not BOT_TOKEN or not CHAT_ID:
        return

    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": msg}
        )
    except:
        pass

# ----------------------------
# Keyword Check
# ----------------------------

def contains_tableau(text):
    return KEYWORD in text.lower()

# ----------------------------
# LinkedIn Scanner (Reliable)
# ----------------------------

def check_linkedin():

    url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

    params = {
        "keywords": "tableau",
        "location": "Pune",
        "f_TPR": "r86400"
    }

    try:
        r = requests.get(url, params=params)
        ids = re.findall(r'jobPosting:(\d+)', r.text)

        for job_id in ids:

            link = f"https://www.linkedin.com/jobs/view/{job_id}"

            if link in SEEN:
                continue

            SEEN.add(link)
            save_seen()

            send(f"Tableau Job — LinkedIn\n{link}")

    except:
        pass

# ----------------------------
# Citi Scanner
# ----------------------------

def check_citi():

    try:
        url = "https://jobs.citi.com/api/jobs"
        params = {"location": "Pune"}

        data = requests.get(url, params=params).json()

        for job in data.get("jobs", []):

            title = job.get("title", "")
            location = job.get("location", "").lower()
            link = job.get("applyUrl", "")

            if LOCATION not in location:
                continue

            if not contains_tableau(title):
                continue

            if link in SEEN:
                continue

            SEEN.add(link)
            save_seen()

            send(f"Tableau Job — Citi\n{link}")

    except:
        pass

# ----------------------------
# CRON TRIGGER ROUTE
# ----------------------------

@app.route("/")
def trigger():

    print("Cron triggered scan")

    check_linkedin()
    check_citi()

    return "Scan complete"

# ----------------------------
# REQUIRED FOR RENDER
# ----------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
