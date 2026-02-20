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
# Persistent storage
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

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    try:

        requests.post(url, json={

            "chat_id": CHAT_ID,

            "text": message

        })

        print("Alert sent")

    except Exception as e:

        print("Telegram error:", e)


# -------------------------
# Keyword match in full text
# -------------------------

def contains_tableau(text):

    return KEYWORD in text.lower()


# -------------------------
# Flask app (Render required)
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

        "keywords": "",

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

        try:

            job_page = requests.get(link)

            full_text = job_page.text.lower()

            if not contains_tableau(full_text):

                continue

            SEEN_JOBS.add(link)

            save_seen_jobs()

            send_telegram(

f"""Tableau Job Found — LinkedIn

Apply:
{link}"""
            )

        except:

            pass


# -------------------------
# WORKDAY SCANNER
# -------------------------

WORKDAY_URLS = [

("Deloitte USI",

"https://deloitte.wd1.myworkdayjobs.com/wday/cxs/deloitte/USIExternalCareerSite/jobs"),

("Barclays",

"https://barclays.wd3.myworkdayjobs.com/wday/cxs/barclays/External_Career_Site/jobs"),

("Mastercard",

"https://mastercard.wd1.myworkdayjobs.com/wday/cxs/mastercard/CorporateCareers/jobs")

]


def check_workday():

    print("Checking Workday companies")

    for company, api_url in WORKDAY_URLS:

        try:

            response = requests.get(api_url)

            data = response.json()

            for job in data.get("jobPostings", []):

                location = job.get("locationsText","").lower()

                if LOCATION not in location:

                    continue

                job_path = job.get("externalPath","")

                full_link = api_url.split("/wday")[0] + job_path

                if full_link in SEEN_JOBS:

                    continue

                try:

                    job_page = requests.get(full_link)

                    full_text = job_page.text.lower()

                    if not contains_tableau(full_text):

                        continue

                    SEEN_JOBS.add(full_link)

                    save_seen_jobs()

                    send_telegram(

f"""Tableau Job Found — {company}

Apply:
{full_link}"""
                    )

                except:

                    pass

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

            link = job.get("applyUrl","")

            if link in SEEN_JOBS:

                continue

            job_page = requests.get(link)

            full_text = job_page.text.lower()

            if not contains_tableau(full_text):

                continue

            SEEN_JOBS.add(link)

            save_seen_jobs()

            send_telegram(

f"""Tableau Job Found — Citi

Apply:
{link}"""
            )

    except Exception as e:

        print("Citi error:", e)


# -------------------------
# MAERSK SCANNER
# -------------------------

def check_maersk():

    print("Checking Maersk")

    try:

        url = "https://www.maersk.com/careers/vacancies"

        page = requests.get(url)

        links = re.findall(

            r'href="(/careers/vacancies/[^\"]+)"',

            page.text

        )

        for path in links:

            link = "https://www.maersk.com" + path

            if link in SEEN_JOBS:

                continue

            job_page = requests.get(link)

            full_text = job_page.text.lower()

            if not contains_tableau(full_text):

                continue

            SEEN_JOBS.add(link)

            save_seen_jobs()

            send_telegram(

f"""Tableau Job Found — Maersk

Apply:
{link}"""
            )

    except:

        pass


# -------------------------
# PEPSICO SCANNER
# -------------------------

def check_pepsico():

    print("Checking PepsiCo")

    try:

        url = "https://www.pepsicojobs.com/main/jobs"

        page = requests.get(url)

        links = re.findall(

            r'href="(/main/job/[^\"]+)"',

            page.text

        )

        for path in links:

            link = "https://www.pepsicojobs.com" + path

            if link in SEEN_JOBS:

                continue

            job_page = requests.get(link)

            full_text = job_page.text.lower()

            if not contains_tableau(full_text):

                continue

            SEEN_JOBS.add(link)

            save_seen_jobs()

            send_telegram(

f"""Tableau Job Found — PepsiCo

Apply:
{link}"""
            )

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
# Background thread
# -------------------------

def run_bot():

    threading.Thread(target=job_checker).start()


# -------------------------
# Start app
# -------------------------

if __name__ == "__main__":

    run_bot()

    port = int(os.environ.get("PORT", 10000))

    app.run(host="0.0.0.0", port=port)
