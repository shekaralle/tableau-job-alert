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
    return "Global Job Alert Bot Running"

# Telegram alert
def send_telegram(message):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": message
    }

    requests.post(url, data=data)


# WORKDAY companies
WORKDAY_COMPANIES = [
    "genpact",
    "mastercard",
    "barclays",
    "accenture",
    "wipro",
    "infosys",
    "deloitte",
    "ey",
    "pwc",
    "kpmg",
    "amazon",
    "citi"
]

def check_workday():

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

                process_job(company, title, location, link)

        except:
            pass


# GREENHOUSE companies
GREENHOUSE_COMPANIES = [
    "coinbase",
    "airbnb",
    "stripe",
    "shopify",
    "twilio",
    "databricks",
    "doordash"
]

def check_greenhouse():

    for company in GREENHOUSE_COMPANIES:

        url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"

        try:

            response = requests.get(url)

            data = response.json()

            for job in data.get("jobs", []):

                title = job.get("title", "")
                location = job.get("location", {}).get("name", "")
                link = job.get("absolute_url", "")

                process_job(company, title, location, link)

        except:
            pass


# LEVER companies
LEVER_COMPANIES = [
    "netflix",
    "canva",
    "atlassian",
    "uber",
    "palantir"
]

def check_lever():

    for company in LEVER_COMPANIES:

        url = f"https://api.lever.co/v0/postings/{company}?mode=json"

        try:

            response = requests.get(url)

            data = response.json()

            for job in data:

                title = job.get("text", "")
                location = job.get("categories", {}).get("location", "")
                link = job.get("hostedUrl", "")

                process_job(company, title, location, link)

        except:
            pass


# Microsoft
def check_microsoft():

    url = "https://gcsservices.careers.microsoft.com/search/api/v1/search"

    try:

        params = {"l": "Pune"}

        response = requests.get(url, params=params)

        data = response.json()

        for job in data.get("operationResult", {}).get("result", {}).get("jobs", []):

            title = job.get("title", "")
            location = job.get("properties", {}).get("locations", [""])[0]
            link = f"https://jobs.careers.microsoft.com/global/en/job/{job.get('jobId')}"

            process_job("Microsoft", title, location, link)

    except:
        pass


# Google
def check_google():

    url = "https://careers.google.com/api/v3/search/"

    try:

        response = requests.get(url)

        data = response.json()

        for job in data.get("jobs", []):

            title = job.get("title", "")
            location = job.get("locations", [""])[0]
            link = job.get("apply_url", "")

            process_job("Google", title, location, link)

    except:
        pass


# Common processor
def process_job(company, title, location, link):

    if LOCATION.lower() in location.lower():

        for keyword in KEYWORDS:

            if keyword.lower() in title.lower():

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


# Main loop
def job_checker():

    send_telegram("Global Job Alert Bot Started")

    while True:

        print("Scanning all career websites...")

        check_workday()
        check_greenhouse()
        check_lever()
        check_microsoft()
        check_google()

        time.sleep(300)


def run_bot():
    threading.Thread(target=job_checker).start()


if __name__ == "__main__":

    run_bot()

    port = int(os.environ.get("PORT", 10000))

    app.run(host="0.0.0.0", port=port)
