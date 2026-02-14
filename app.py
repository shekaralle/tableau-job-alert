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


# TELEGRAM ALERT
def send_telegram(message):

    if not BOT_TOKEN or not CHAT_ID:
        print("Telegram credentials missing")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": message
    }

    try:
        requests.post(url, data=data)
    except Exception as e:
        print(e)


# LINKEDIN SCANNER
def check_linkedin():

    print("Checking LinkedIn...")

    url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

    params = {
        "keywords": "Tableau",
        "location": "Pune",
        "start": 0
    }

    try:

        response = requests.get(url, params=params)

        text = response.text

        jobs = text.split("href=")

        for job in jobs:

            if "linkedin.com/jobs/view" in job:

                link = job.split('"')[1]

                if link not in SEEN_JOBS:

                    SEEN_JOBS.add(link)

                    message = f"""
New Tableau Job Found on LinkedIn!

Location: Pune

Apply: {link}
"""

                    send_telegram(message)

    except Exception as e:
        print(e)


# WORKDAY SCANNER
WORKDAY_COMPANIES = [
    "genpact",
    "mastercard",
    "barclays",
    "accenture",
    "infosys",
    "wipro",
    "deloitte",
    "ey",
    "pwc",
    "citi"
]

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

                if LOCATION.lower() in location.lower() and "tableau" in title.lower():

                    if link not in SEEN_JOBS:

                        SEEN_JOBS.add(link)

                        message = f"""
New Tableau Job Found!

Company: {company}
Title: {title}
Location: {location}

Apply: {link}
"""

                        send_telegram(message)

        except Exception as e:
            print(e)


# MAIN LOOP
def job_checker():

    send_telegram("Job Alert Bot Started Successfully")

    while True:

        print("Scanning all websites...")

        check_linkedin()
        check_workday()

        time.sleep(300)


def run_bot():
    threading.Thread(target=job_checker).start()


if __name__ == "__main__":

    run_bot()

    port = int(os.environ.get("PORT", 10000))

    app.run(host="0.0.0.0", port=port)
