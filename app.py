import requests
import os
import re
import json
from flask import Flask

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

LOCATION = "pune"
KEYWORD = "tableau"

SEEN_FILE = "seen_jobs.json"

# --------------------------
# Load & Save Seen Jobs
# --------------------------

def load_seen_jobs():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen_jobs():
    with open(SEEN_FILE, "w") as f:
        json.dump(list(SEEN_JOBS), f)

SEEN_JOBS = load_seen_jobs()

# --------------------------
# Telegram Alert
# --------------------------

def send_telegram(message):

    if not BOT_TOKEN or not CHAT_ID:
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    try:
        requests.post(url, json={
            "chat_id": CHAT_ID,
            "text": message
        })
    except:
        pass

# --------------------------
# Keyword Check
# --------------------------

def contains_tableau(text):
    return KEYWORD in text.lower()

# --------------------------
# LINKEDIN
# --------------------------

def check_linkedin():

    url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

    params = {
        "keywords": "tableau",
        "location": "Pune",
        "f_TPR": "r86400"
    }

    response = requests.get(url, params=params)

    job_ids = re.findall(
        r'data-entity-urn="urn:li:jobPosting:(\d+)"',
        response.text
    )

    for job_id in job_ids:

        link = f"https://www.linkedin.com/jobs/view/{job_id}"

        if link in SEEN_JOBS:
            continue

        SEEN_JOBS.add(link)
        save_seen_jobs()

        send_telegram(f"Tableau Job — LinkedIn\n{link}")

# --------------------------
# WORKDAY (Deloitte, Barclays, Mastercard)
# --------------------------

WORKDAY_COMPANIES = [

("Deloitte USI",
"https://deloitte.wd1.myworkdayjobs.com/wday/cxs/deloitte/USIExternalCareerSite/jobs"),

("Barclays",
"https://barclays.wd3.myworkdayjobs.com/wday/cxs/barclays/External_Career_Site/jobs"),

("Mastercard",
"https://mastercard.wd1.myworkdayjobs.com/wday/cxs/mastercard/CorporateCareers/jobs")

]

def check_workday():

    for company, api_url in WORKDAY_COMPANIES:

        try:

            response = requests.get(api_url)

            if response.status_code != 200:
                continue

            data = response.json()

            for job in data.get("jobPostings", []):

                location = job.get("locationsText", "").lower()

                if LOCATION not in location:
                    continue

                title = job.get("title", "")
                link = api_url.split("/wday")[0] + job.get("externalPath", "")

                if link in SEEN_JOBS:
                    continue

                # Workday already filters by title search internally,
                # so we check title only (stable approach)
                if not contains_tableau(title):
                    continue

                SEEN_JOBS.add(link)
                save_seen_jobs()

                send_telegram(
f"""Tableau Job — {company}

Title: {title}

{link}"""
                )

        except:
            pass

# --------------------------
# CITI
# --------------------------

def check_citi():

    try:

        url = "https://jobs.citi.com/api/jobs"

        params = {
            "location": "Pune"
        }

        data = requests.get(url, params=params).json()

        for job in data.get("jobs", []):

            title = job.get("title", "")
            location = job.get("location", "").lower()
            link = job.get("applyUrl", "")

            if LOCATION not in location:
                continue

            if not contains_tableau(title):
                continue

            if link in SEEN_JOBS:
                continue

            SEEN_JOBS.add(link)
            save_seen_jobs()

            send_telegram(f"Tableau Job — Citi\n{link}")

    except:
        pass

# --------------------------
# FLASK ROUTE (CRON TRIGGER)
# --------------------------

app = Flask(__name__)

@app.route("/")
def trigger_scan():

    print("Cron triggered scan")

    check_linkedin()
    check_workday()
    check_citi()

    return "Scan completed"
