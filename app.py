import requests
import time
import os
import threading
import re
from flask import Flask
from datetime import datetime, timedelta, timezone

# Telegram credentials from Render environment
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# Filters
KEYWORDS = ["tableau"]
LOCATION = "pune"

# Only jobs from last 12 hours
TIME_THRESHOLD = datetime.now(timezone.utc) - timedelta(hours=12)

# Store seen jobs to avoid duplicates
SEEN_JOBS = set()

# Flask app required for Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Job Alert Bot Running"


# TELEGRAM ALERT FUNCTION
def send_telegram(message):

    if not BOT_TOKEN or not CHAT_ID:
        print("Missing Telegram credentials")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": message
    }

    try:
        requests.post(url, data=data)
        print("Alert sent")
    except Exception as e:
        print("Telegram error:", e)


# CHECK IF JOB IS WITHIN LAST 12 HOURS
def is_recent(timestamp_ms):

    try:

        job_time = datetime.fromtimestamp(
            timestamp_ms / 1000,
            timezone.utc
        )

        return job_time >= TIME_THRESHOLD

    except:
        return False


# LINKEDIN SCANNER
def check_linkedin():

    print("Checking LinkedIn...")

    url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

    params = {
        "keywords": "Tableau",
        "location": "Pune",
        "f_TPR": "r43200",  # last 12 hours
        "start": 0
    }

    try:

        response = requests.get(url, params=params)

        html = response.text

        # Extract job IDs safely
        job_ids = re.findall(
            r'data-entity-urn="urn:li:jobPosting:(\d+)"',
            html
        )

        for job_id in job_ids:

            link = f"https://www.linkedin.com/jobs/view/{job_id}"

            if link not in SEEN_JOBS:

                SEEN_JOBS.add(link)

                message = f"""
New Tableau Job — LinkedIn
Location: Pune
Posted: Last 12 hours

Apply:
{link}
"""

                send_telegram(message)

    except Exception as e:
        print("LinkedIn error:", e)


# WORKDAY COMPANIES
WORKDAY_COMPANIES = [
    "genpact",
    "mastercard",
    "barclays",
    "accenture",
    "infosys",
    "wipro",
    "deloitte",
    "ey",
    "pwc"
]


# WORKDAY SCANNER
def check_workday():

    print("Checking Workday companies...")

    for company in WORKDAY_COMPANIES:

        url = f"https://{company}.wd5.myworkdayjobs.com/wday/cxs/{company}/{company}/jobs"

        try:

            response = requests.get(url)

            if response.status_code != 200:
                continue

            data = response.json()

            for job in data.get("jobPostings", []):

                title = job.get("title", "")
                location = job.get("locationsText", "")
                link = f"https://{company}.wd5.myworkdayjobs.com{job.get('externalPath','')}"

                posted_time = job.get("postedOn", 0)

                if not posted_time:
                    continue

                # Only recent jobs
                if isinstance(posted_time, int):
                    if not is_recent(posted_time):
                        continue

                # Apply filters
                if LOCATION.lower() in location.lower() and any(
                    skill in title.lower() for skill in KEYWORDS
                ):

                    if link not in SEEN_JOBS:

                        SEEN_JOBS.add(link)

                        message = f"""
New Tableau Job — Workday

Company: {company}
Title: {title}
Location: {location}
Posted: Last 12 hours

Apply:
{link}
"""

                        send_telegram(message)

        except Exception as e:
            print(f"{company} error:", e)


# MAIN LOOP
def job_checker():

    send_telegram(
        "Job Alert Bot Started — Monitoring LinkedIn + Workday (Last 12 hrs)"
    )

    while True:

        print("Scanning jobs...")

        check_linkedin()
        check_workday()

        print("Sleeping 5 minutes...\n")

        time.sleep(300)


# START BACKGROUND THREAD
def run_bot():
    threading.Thread(target=job_checker).start()


# MAIN ENTRY
if __name__ == "__main__":

    run_bot()

    port = int(os.environ.get("PORT", 10000))

    app.run(host="0.0.0.0", port=port)
