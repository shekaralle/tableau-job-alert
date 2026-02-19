import requests
import time
import os
import re
import json
from datetime import datetime, timedelta, timezone
from flask import Flask
import threading

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

KEYWORDS = ["tableau"]
LOCATION = "pune"

SEEN_FILE = "seen_jobs.json"

def load_seen_jobs():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen_jobs():
    with open(SEEN_FILE, "w") as f:
        json.dump(list(SEEN_JOBS), f)

SEEN_JOBS = load_seen_jobs()

app = Flask(__name__)

@app.route("/")
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
        print("Alert sent")
    except Exception as e:
        print(e)


def keyword_match(title):

    return any(keyword in title.lower() for keyword in KEYWORDS)


# LINKEDIN
def check_linkedin():

    print("Scanning LinkedIn")

    url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

    params = {
        "keywords": "Tableau",
        "location": "Pune",
        "f_TPR": "r43200"
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

        send_telegram(f"LinkedIn Tableau Job\n{link}")


# WORKDAY
WORKDAY_URLS = [

("Deloitte USI",
"https://deloitte.wd1.myworkdayjobs.com/wday/cxs/deloitte/USIExternalCareerSite/jobs"),

("Barclays",
"https://barclays.wd3.myworkdayjobs.com/wday/cxs/barclays/External_Career_Site/jobs"),

("Mastercard CorporateCareers",
"https://mastercard.wd1.myworkdayjobs.com/wday/cxs/mastercard/CorporateCareers/jobs")

]


def check_workday():

    print("Scanning Workday")

    for company, url in WORKDAY_URLS:

        try:

            data = requests.get(url).json()

            for job in data.get("jobPostings", []):

                title = job.get("title","")
                location = job.get("locationsText","")

                if LOCATION not in location.lower():
                    continue

                if not keyword_match(title):
                    continue

                link = url.split("/wday")[0] + job.get("externalPath","")

                if link in SEEN_JOBS:
                    continue

                SEEN_JOBS.add(link)
                save_seen_jobs()

                send_telegram(
f"""Workday Tableau Job

Company: {company}
Title: {title}

{link}"""
                )

        except Exception as e:
            print(company, e)


# BARCLAYS PORTAL
def check_barclays_portal():

    print("Scanning Barclays Portal")

    try:

        url = "https://search.jobs.barclays/search-jobs/Pune"

        response = requests.get(url)

        jobs = re.findall(
            r'<a class="job-title".*?href="([^"]+)".*?>(.*?)</a>',
            response.text,
            re.DOTALL
        )

        for link_path, title in jobs:

            title_clean = re.sub('<.*?>', '', title).strip()

            if not keyword_match(title_clean):
                continue

            link = "https://search.jobs.barclays" + link_path

            if link in SEEN_JOBS:
                continue

            SEEN_JOBS.add(link)
            save_seen_jobs()

            send_telegram(
f"""Barclays Tableau Job

Title: {title_clean}

{link}"""
            )

    except Exception as e:
        print(e)


# CITI
def check_citi():

    print("Scanning Citi")

    try:

        url = "https://jobs.citi.com/api/jobs"

        params = {"location":"Pune"}

        data = requests.get(url, params=params).json()

        for job in data.get("jobs", []):

            title = job.get("title","")
            location = job.get("location","")
            link = job.get("applyUrl","")

            if LOCATION not in location.lower():
                continue

            if not keyword_match(title):
                continue

            if link in SEEN_JOBS:
                continue

            SEEN_JOBS.add(link)
            save_seen_jobs()

            send_telegram(
f"""Citi Tableau Job

Title: {title}

{link}"""
            )

    except Exception as e:
        print(e)


# MAERSK
def check_maersk():

    print("Scanning Maersk")

    try:

        url = "https://www.maersk.com/careers/vacancies"

        response = requests.get(url)

        jobs = re.findall(
            r'href="(/careers/vacancies/[^"]+)".*?>(.*?)</a>',
            response.text,
            re.DOTALL
        )

        for link_path, title in jobs:

            title_clean = re.sub('<.*?>', '', title).strip()

            if not keyword_match(title_clean):
                continue

            link = "https://www.maersk.com" + link_path

            if link in SEEN_JOBS:
                continue

            SEEN_JOBS.add(link)
            save_seen_jobs()

            send_telegram(
f"""Maersk Tableau Job

Title: {title_clean}

{link}"""
            )

    except Exception as e:
        print(e)


# PEPSICO
def check_pepsico():

    print("Scanning PepsiCo")

    try:

        url = "https://www.pepsicojobs.com/main/jobs"

        response = requests.get(url)

        jobs = re.findall(
            r'href="(/main/job/[^"]+)".*?>(.*?)</a>',
            response.text,
            re.DOTALL
        )

        for link_path, title in jobs:

            title_clean = re.sub('<.*?>', '', title).strip()

            if not keyword_match(title_clean):
                continue

            link = "https://www.pepsicojobs.com" + link_path

            if link in SEEN_JOBS:
                continue

            SEEN_JOBS.add(link)
            save_seen_jobs()

            send_telegram(
f"""PepsiCo Tableau Job

Title: {title_clean}

{link}"""
            )

    except Exception as e:
        print(e)


# MAIN LOOP
def job_checker():

    send_telegram("Bot started - monitoring Tableau jobs in Pune")

    while True:

        check_linkedin()
        check_workday()
        check_barclays_portal()
        check_citi()
        check_maersk()
        check_pepsico()

        print("Sleeping 5 minutes")

        time.sleep(300)


def run_bot():
    threading.Thread(target=job_checker).start()


if __name__ == "__main__":

    run_bot()

    port = int(os.environ.get("PORT",10000))

    app.run(host="0.0.0.0", port=port)
