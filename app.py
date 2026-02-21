import requests
import time
import os
import re
import json
import threading
from flask import Flask

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

LOCATION = "pune"
KEYWORD = "tableau"

SEEN_FILE = "seen_jobs.json"

# -------------------------
# Load seen jobs
# -------------------------

def load_seen_jobs():

    if os.path.exists(SEEN_FILE):

        with open(SEEN_FILE, "r") as f:

            return set(json.load(f))

    return set()


def save_seen_jobs():

    with open(SEEN_FILE, "w") as f:

        json.dump(list(SEEN_JOBS), f)


SEEN_JOBS = load_seen_jobs()

# -------------------------
# Telegram alert
# -------------------------

def send_telegram(message):

    try:

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        requests.post(url, json={

            "chat_id": CHAT_ID,

            "text": message

        })

        print("Alert sent")

    except Exception as e:

        print("Telegram error:", e)


# -------------------------
# Keyword matcher
# -------------------------

def contains_tableau(text):

    return KEYWORD in text.lower()


# -------------------------
# Flask app
# -------------------------

app = Flask(__name__)

@app.route("/")
def home():

    return "Tableau Job Bot Running"


# -------------------------
# LINKEDIN SCANNER
# -------------------------

def check_linkedin():

    print("Checking LinkedIn")

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

        send_telegram(f"Tableau Job Found — LinkedIn\n{link}")


# -------------------------
# WORKDAY SCANNER
# -------------------------

WORKDAY_COMPANIES = [

("Deloitte USI",
"https://deloitte.wd1.myworkdayjobs.com/wday/cxs/deloitte/USIExternalCareerSite/jobs"),

("Barclays",
"https://barclays.wd3.myworkdayjobs.com/wday/cxs/barclays/External_Career_Site/jobs"),

("Mastercard",
"https://mastercard.wd1.myworkdayjobs.com/wday/cxs/mastercard/CorporateCareers/jobs")

]


def check_workday():

    print("Checking Workday companies")

    for company, api_url in WORKDAY_COMPANIES:

        try:

            response = requests.get(api_url)

            if response.status_code != 200:

                print("Failed:", company)

                continue

            data = response.json()

            for job in data.get("jobPostings", []):

                location = job.get("locationsText", "").lower()

                if LOCATION not in location:
                    continue

                title = job.get("title", "")

                external_path = job.get("externalPath", "")

                public_link = api_url.split("/wday")[0] + external_path

                if public_link in SEEN_JOBS:
                    continue

                # Fetch detail API (correct endpoint)
                detail_api = api_url.split("/jobs")[0] + external_path.replace("/job/", "/jobPosting/")

                detail_response = requests.get(detail_api)

                detail_text = detail_response.text.lower()

                full_text = title.lower() + " " + detail_text

                if not contains_tableau(full_text):
                    continue

                SEEN_JOBS.add(public_link)
                save_seen_jobs()

                send_telegram(
f"""Tableau Job Found — {company}

Title: {title}

Apply:
{public_link}"""
                )

        except Exception as e:

            print(company, "error:", e)


# -------------------------
# CITI SCANNER
# -------------------------

def check_citi():

    print("Checking Citi")

    try:

        url = "https://jobs.citi.com/api/jobs"

        params = {

            "location": "Pune",

            "limit": 50

        }

        data = requests.get(url, params=params).json()

        for job in data.get("jobs", []):

            title = job.get("title", "")

            link = job.get("applyUrl", "")

            location = job.get("location", "").lower()

            if LOCATION not in location:
                continue

            if link in SEEN_JOBS:
                continue

            detail = requests.get(link).text.lower()

            if not contains_tableau(title + detail):
                continue

            SEEN_JOBS.add(link)
            save_seen_jobs()

            send_telegram(f"Tableau Job Found — Citi\n{link}")

    except Exception as e:

        print("Citi error:", e)


# -------------------------
# MAERSK SCANNER
# -------------------------

def check_maersk():

    print("Checking Maersk")

    try:

        page = requests.get("https://www.maersk.com/careers/vacancies")

        links = re.findall(r'href="(/careers/vacancies/[^\"]+)"', page.text)

        for path in links:

            link = "https://www.maersk.com" + path

            if link in SEEN_JOBS:
                continue

            detail = requests.get(link).text.lower()

            if not contains_tableau(detail):
                continue

            SEEN_JOBS.add(link)
            save_seen_jobs()

            send_telegram(f"Tableau Job Found — Maersk\n{link}")

    except:
        pass


# -------------------------
# PEPSICO SCANNER
# -------------------------

def check_pepsico():

    print("Checking PepsiCo")

    try:

        page = requests.get("https://www.pepsicojobs.com/main/jobs")

        links = re.findall(r'href="(/main/job/[^\"]+)"', page.text)

        for path in links:

            link = "https://www.pepsicojobs.com" + path

            if link in SEEN_JOBS:
                continue

            detail = requests.get(link).text.lower()

            if not contains_tableau(detail):
                continue

            SEEN_JOBS.add(link)
            save_seen_jobs()

            send_telegram(f"Tableau Job Found — PepsiCo\n{link}")

    except:
        pass


# -------------------------
# MAIN LOOP
# -------------------------

def job_checker():

    send_telegram("Tableau Job Bot Started")

    while True:

        print("Scanning all companies")

        check_linkedin()

        check_workday()

        check_citi()

        check_maersk()

        check_pepsico()

        print("Sleeping 5 minutes")

        time.sleep(300)


# -------------------------
# Run bot
# -------------------------

def run_bot():

    threading.Thread(target=job_checker).start()


if __name__ == "__main__":

    run_bot()

    port = int(os.environ.get("PORT", 10000))

    app.run(host="0.0.0.0", port=port)
