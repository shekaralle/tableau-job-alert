import requests
import time
import os
import threading
import re
import json
from flask import Flask
from datetime import datetime, timedelta, timezone

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

KEYWORDS = ["tableau"]
LOCATION = "pune"

TIME_THRESHOLD = datetime.now(timezone.utc) - timedelta(hours=12)

SEEN_FILE = "seen_jobs.json"

# Load seen jobs from file
def load_seen_jobs():

    if os.path.exists(SEEN_FILE):

        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))

    return set()

# Save seen jobs
def save_seen_jobs():

    with open(SEEN_FILE, "w") as f:
        json.dump(list(SEEN_JOBS), f)

SEEN_JOBS = load_seen_jobs()

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

    try:
        requests.post(url, data=data)
    except Exception as e:
        print(e)


def is_recent(posted_time_ms):

    job_time = datetime.fromtimestamp(
        posted_time_ms / 1000,
        timezone.utc
    )

    return job_time >= TIME_THRESHOLD


# FIXED LINKEDIN SCANNER
def check_linkedin():

    print("Checking LinkedIn")

    url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

    params = {
        "keywords": "Tableau",
        "location": "Pune",
        "f_TPR": "r43200"
    }

    response = requests.get(url, params=params)

    html = response.text

    job_ids = re.findall(
        r'data-entity-urn="urn:li:jobPosting:(\d+)"',
        html
    )

    for job_id in job_ids:

        link = f"https://www.linkedin.com/jobs/view/{job_id}"

        if link in SEEN_JOBS:
            continue

        SEEN_JOBS.add(link)
        save_seen_jobs()

        send_telegram(
            f"LinkedIn Tableau Job (Last 12 hrs)\n{link}"
        )


# CORRECT WORKDAY ENDPOINTS
WORKDAY_URLS = [
    ("Genpact", "https://genpact.wd5.myworkdayjobs.com/wday/cxs/genpact/genpactcareers/jobs"),
    ("Mastercard", "https://mastercard.wd1.myworkdayjobs.com/wday/cxs/mastercard/mastercardcareers/jobs"),
    ("Barclays", "https://barclays.wd3.myworkdayjobs.com/wday/cxs/barclays/barclayscareers/jobs"),
    ("Citi", "https://citi.wd3.myworkdayjobs.com/wday/cxs/citi/citicareers/jobs"),
    ("Salesforce", "https://careers.salesforce.com/en/jobs/?search=")
]


def check_workday():

    print("Checking Workday")

    for company, url in WORKDAY_URLS:

        try:

            response = requests.get(url)

            data = response.json()

            for job in data.get("jobPostings", []):

                title = job["title"]
                location = job["locationsText"]

                link = url.split("/wday")[0] + job["externalPath"]

                posted = job.get("postedOn")

                if not posted:
                    continue

                if not is_recent(posted):
                    continue

                if LOCATION.lower() not in location.lower():
                    continue

                if "tableau" not in title.lower():
                    continue

                if link in SEEN_JOBS:
                    continue

                SEEN_JOBS.add(link)
                save_seen_jobs()

                send_telegram(
                    f"""
Workday Tableau Job

Company: {company}
Title: {title}
Location: {location}

Apply:
{link}
"""
                )

        except Exception as e:

            print(company, "error:", e)


def job_checker():

    send_telegram("Bot Started — Monitoring Tableau Jobs Pune")

    while True:

        check_linkedin()
        check_workday()

        time.sleep(300)


def run_bot():
    threading.Thread(target=job_checker).start()


if __name__ == "__main__":

    run_bot()

    port = int(os.environ.get("PORT", 10000))

    app.run(host="0.0.0.0", port=port)
