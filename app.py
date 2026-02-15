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

TIME_THRESHOLD = datetime.now(timezone.utc) - timedelta(hours=12)

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


def is_recent(timestamp):

    try:
        job_time = datetime.fromtimestamp(
            timestamp / 1000,
            timezone.utc
        )
        return job_time >= TIME_THRESHOLD
    except:
        return True


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

("Genpact",
"https://genpact.wd5.myworkdayjobs.com/wday/cxs/genpact/genpactcareers/jobs"),

("Barclays",
"https://barclays.wd3.myworkdayjobs.com/wday/cxs/barclays/barclayscareers/jobs"),

("Infosys",
"https://infosys.wd5.myworkdayjobs.com/wday/cxs/infosys/InfosysCareers/jobs"),

("Deloitte",
"https://deloitte.wd1.myworkdayjobs.com/wday/cxs/deloitte/DeloitteCareers/jobs"),

("EY",
"https://ey.wd3.myworkdayjobs.com/wday/cxs/ey/EYCareers/jobs"),

("PwC",
"https://pwc.wd3.myworkdayjobs.com/wday/cxs/pwc/PwCCareers/jobs"),

("Accenture",
"https://accenture.wd3.myworkdayjobs.com/wday/cxs/accenture/AccentureCareers/jobs"),

("Wipro",
"https://wipro.wd5.myworkdayjobs.com/wday/cxs/wipro/WiproCareers/jobs")

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

                if "tableau" not in title.lower():
                    continue

                link = url.split("/wday")[0] + job.get("externalPath","")

                if link in SEEN_JOBS:
                    continue

                SEEN_JOBS.add(link)
                save_seen_jobs()

                send_telegram(
f"""Workday Job

Company: {company}
Title: {title}

{link}"""
                )

        except Exception as e:
            print(company, e)


# CITI
def check_citi():

    print("Scanning Citi")

    try:

        url = "https://jobs.citi.com/api/jobs"

        params = {
            "keywords":"Tableau",
            "location":"Pune"
        }

        data = requests.get(url, params=params).json()

        for job in data.get("jobs",[]):

            link = job.get("applyUrl","")

            if link in SEEN_JOBS:
                continue

            SEEN_JOBS.add(link)
            save_seen_jobs()

            send_telegram(f"Citi Job\n{link}")

    except Exception as e:
        print(e)


# SALESFORCE
def check_salesforce():

    print("Scanning Salesforce")

    try:

        data = requests.get(
"https://careers.salesforce.com/api/jobs"
        ).json()

        for job in data.get("jobs",[]):

            title = job.get("title","")
            location = job.get("location","")
            link = job.get("url","")

            if LOCATION not in location.lower():
                continue

            if "tableau" not in title.lower():
                continue

            if link in SEEN_JOBS:
                continue

            SEEN_JOBS.add(link)
            save_seen_jobs()

            send_telegram(f"Salesforce Job\n{link}")

    except Exception as e:
        print(e)


# MICROSOFT
def check_microsoft():

    print("Scanning Microsoft")

    try:

        url = "https://gcsservices.careers.microsoft.com/search/api/v1/search"

        params = {"l":"Pune"}

        data = requests.get(url,params=params).json()

        jobs = data.get("operationResult",{}).get("result",{}).get("jobs",[])

        for job in jobs:

            title = job.get("title","")

            if "tableau" not in title.lower():
                continue

            job_id = job.get("jobId")

            link = f"https://jobs.careers.microsoft.com/global/en/job/{job_id}"

            if link in SEEN_JOBS:
                continue

            SEEN_JOBS.add(link)
            save_seen_jobs()

            send_telegram(f"Microsoft Job\n{link}")

    except Exception as e:
        print(e)


# GOOGLE
def check_google():

    print("Scanning Google")

    try:

        data = requests.get(
"https://careers.google.com/api/v3/search/"
        ).json()

        for job in data.get("jobs",[]):

            title = job.get("title","")
            locations = job.get("locations",[])
            link = job.get("apply_url","")

            if not any("pune" in loc.lower() for loc in locations):
                continue

            if "tableau" not in title.lower():
                continue

            if link in SEEN_JOBS:
                continue

            SEEN_JOBS.add(link)
            save_seen_jobs()

            send_telegram(f"Google Job\n{link}")

    except Exception as e:
        print(e)


# MASTERCard NEW
def check_mastercard():

    print("Scanning Mastercard")

    try:

        url = "https://mastercard.wd1.myworkdayjobs.com/wday/cxs/mastercard/mastercardcareers/jobs"

        data = requests.get(url).json()

        for job in data.get("jobPostings", []):

            title = job.get("title","")
            location = job.get("locationsText","")

            if LOCATION not in location.lower():
                continue

            if "tableau" not in title.lower():
                continue

            link = "https://careers.mastercard.com" + job.get("externalPath","")

            if link in SEEN_JOBS:
                continue

            SEEN_JOBS.add(link)
            save_seen_jobs()

            send_telegram(f"Mastercard Job\n{link}")

    except Exception as e:
        print(e)


# MAIN LOOP
def job_checker():

    send_telegram("Bot started - monitoring all companies")

    while True:

        check_linkedin()
        check_workday()
        check_citi()
        check_salesforce()
        check_microsoft()
        check_google()
        check_mastercard()

        print("Sleeping 5 minutes")

        time.sleep(300)


def run_bot():
    threading.Thread(target=job_checker).start()


if __name__ == "__main__":

    run_bot()

    port = int(os.environ.get("PORT",10000))

    app.run(host="0.0.0.0", port=port)
