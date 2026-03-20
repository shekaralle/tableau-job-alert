import requests
import os
import re
import json
from flask import Flask

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

CONFIG_FILE = "config.json"
SEEN_FILE = "seen_jobs.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# -------------------------
# Load config
# -------------------------
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {"keywords": ["tableau"], "locations": ["pune"]}

CONFIG = load_config()

# -------------------------
# Seen jobs
# -------------------------
def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    return set()

def save_seen():
    with open(SEEN_FILE, "w") as f:
        json.dump(list(SEEN), f)

SEEN = load_seen()

# -------------------------
# Telegram
# -------------------------
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

# -------------------------
# Match functions
# -------------------------
def keyword_match(text):
    return any(k.lower() in text.lower() for k in CONFIG["keywords"])

def location_match(text):
    return any(loc.lower() in text.lower() for loc in CONFIG["locations"])

# -------------------------
# LinkedIn
# -------------------------
def check_linkedin():
    for loc in CONFIG["locations"]:
        try:
            url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
            params = {
                "keywords": " ".join(CONFIG["keywords"]),
                "location": loc.title(),
                "f_TPR": "r86400"
            }

            r = requests.get(url, params=params, headers=HEADERS)
            ids = re.findall(r'jobPosting:(\d+)', r.text)

            for job_id in ids:
                link = f"https://www.linkedin.com/jobs/view/{job_id}"

                if link in SEEN:
                    continue

                SEEN.add(link)
                save_seen()

                send(f"LinkedIn Job\n{link}")
        except:
            pass

# -------------------------
# Naukri
# -------------------------
def check_naukri():
    for loc in CONFIG["locations"]:
        try:
            url = f"https://www.naukri.com/{'-'.join(CONFIG['keywords'])}-jobs-in-{loc}"
            page = requests.get(url, headers=HEADERS).text

            links = re.findall(r'href="(https://www.naukri.com/job-listings[^"]+)"', page)

            for link in links:
                if link in SEEN:
                    continue

                SEEN.add(link)
                save_seen()

                send(f"Naukri Job\n{link}")
        except:
            pass

# -------------------------
# Indeed
# -------------------------
def check_indeed():
    for loc in CONFIG["locations"]:
        try:
            query = "+".join(CONFIG["keywords"])
            url = f"https://in.indeed.com/jobs?q={query}&l={loc}"

            page = requests.get(url, headers=HEADERS).text
            links = re.findall(r'/rc/clk\?jk=[^"]+', page)

            for path in links:
                link = "https://in.indeed.com" + path

                if link in SEEN:
                    continue

                SEEN.add(link)
                save_seen()

                send(f"Indeed Job\n{link}")
        except:
            pass

# -------------------------
# Foundit
# -------------------------
def check_foundit():
    for loc in CONFIG["locations"]:
        try:
            query = "-".join(CONFIG["keywords"])
            url = f"https://www.foundit.in/srp/results?query={query}&locations={loc}"

            page = requests.get(url, headers=HEADERS).text
            links = re.findall(r'href="(https://www.foundit.in/job/[^"]+)"', page)

            for link in links:
                if link in SEEN:
                    continue

                SEEN.add(link)
                save_seen()

                send(f"Foundit Job\n{link}")
        except:
            pass

# -------------------------
# Glassdoor
# -------------------------
def check_glassdoor():
    for loc in CONFIG["locations"]:
        try:
            query = "+".join(CONFIG["keywords"])
            url = f"https://www.glassdoor.co.in/Job/jobs.htm?sc.keyword={query}&locT=C&locId=&locKeyword={loc}"

            page = requests.get(url, headers=HEADERS).text
            links = re.findall(r'href="(/partner/jobListing[^"]+)"', page)

            for path in links:
                link = "https://www.glassdoor.co.in" + path

                if link in SEEN:
                    continue

                SEEN.add(link)
                save_seen()

                send(f"Glassdoor Job\n{link}")
        except:
            pass

# -------------------------
# Workday
# -------------------------
WORKDAY = [
    ("Deloitte", "https://deloitte.wd1.myworkdayjobs.com/wday/cxs/deloitte/USIExternalCareerSite/jobs"),
    ("Barclays", "https://barclays.wd3.myworkdayjobs.com/wday/cxs/barclays/External_Career_Site/jobs"),
    ("Mastercard", "https://mastercard.wd1.myworkdayjobs.com/wday/cxs/mastercard/CorporateCareers/jobs")
]

def check_workday():
    for company, url in WORKDAY:
        try:
            data = requests.get(url, headers=HEADERS).json()

            for job in data.get("jobPostings", []):
                title = job.get("title","")
                location = job.get("locationsText","")

                if not keyword_match(title):
                    continue

                if not location_match(location):
                    continue

                link = url.split("/wday")[0] + job.get("externalPath","")

                if link in SEEN:
                    continue

                SEEN.add(link)
                save_seen()

                send(f"{company} Job\n{title}\n{link}")
        except:
            pass

# -------------------------
# Citi
# -------------------------
def check_citi():
    try:
        url = "https://jobs.citi.com/api/jobs"
        params = {
            "keywords": " ".join(CONFIG["keywords"]),
            "location": ",".join(CONFIG["locations"])
        }

        data = requests.get(url, params=params).json()

        for job in data.get("jobs", []):
            link = job.get("applyUrl","")
            title = job.get("title","")

            if link in SEEN:
                continue

            SEEN.add(link)
            save_seen()

            send(f"Citi Job\n{title}\n{link}")
    except:
        pass

# -------------------------
# Tiger Analytics
# -------------------------
def check_tiger():
    try:
        url = "https://www.tigeranalytics.com/about-us/current-openings/"
        page = requests.get(url, headers=HEADERS).text

        links = re.findall(r'href="(https://www.tigeranalytics.com[^"]+)"', page)

        for link in links:

            if link in SEEN:
                continue

            if not keyword_match(link):
                continue

            SEEN.add(link)
            save_seen()

            send(f"Tiger Analytics Job\n{link}")
    except:
        pass

# -------------------------
# Trigger
# -------------------------
@app.route("/")
def run():

    print("Running scan")

    check_linkedin()
    check_naukri()
    check_indeed()
    check_foundit()
    check_glassdoor()
    check_workday()
    check_citi()
    check_tiger()

    return "Done"

# -------------------------
# Render required
# -------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
