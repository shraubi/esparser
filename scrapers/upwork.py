import re
from datetime import timedelta
import time
import logging
import os
import pickle
import feedparser
import pendulum

import requests as req

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import Chrome


BAD_COUNTRIES = ["India", "Pakistan", "Nigeria"]
TIME_IN_PAST = timedelta(minutes=5)
MIN_BUDGET = 600
MAX_RANGE_FROM = 40
senders = [
    os.getenv("UPWORK_IMPORTANT_BOT_TOKEN"),
    os.getenv("UPWORK_ALLPYTHON_BOT_TOKEN"),
]

receivers = str(os.getenv("TG_BOT_RECEIVERS")).split(",")

logging.basicConfig(level=logging.INFO)

SEARCH_QUERIES = [
    ("data+engineer", senders[0]),
    ("ETL", senders[0]),
    ("airflow", senders[0]),
    ("DevOps", senders[0]),
    ("Amazon Web Services", senders[0]),
    ("Amazon EC2", senders[0]),
    ("terraform", senders[0]),
    ("python", senders[1]),
    ("Docker", senders[1]),
    ("GitHub", senders[1]),
    ("GCP", senders[0]),
]

class WebDriver(object):
    def __init__(self):
        self.options = Options()
        self.options.add_argument('--no-sandbox')
        #self.options.binary_location = "/usr/bin/google-chrome"
        self.options.add_argument('--headless')
        self.options.add_argument('--disable-dev-shm-usage')
        user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36"
        self.options.add_argument(f"user-agent={user_agent}")

    def get(self):
        driver = Chrome(executable_path='/app/chromedriver', options=self.options)
        return driver
    
try:
    with open("ad_ids.pkl", 'rb') as f:
        ids = pickle.load(f)
except FileNotFoundError:
    ids = set()

def send_msg(sender, text):
    for chat_id in receivers:
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "Like", "callback_data": "like"},
                    {"text": "Dislike", "callback_data": "dislike"},
                ]
            ]
        }
        payload = {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": True,
            #"reply_markup": keyboard,
        }
        headers = {"accept": "application/json", "content-type": "application/json"}
        url_req = f"https://api.telegram.org/bot{sender}/sendMessage"
        response = req.post(url_req, json=payload, headers=headers)
        if response.status_code != 200:
            logging.warning(
                f"got {response.status_code} with {response.text}. payload {payload}")
        print('sent', chat_id)


def parse_with_selenium(urls, sender):

    instance_ = WebDriver()
    driver = instance_.get()
    
    def login():
        driver.get("https://www.upwork.com/ab/account-security/login")
        time.sleep(3)
        driver.find_element(By.CLASS_NAME, "up-input").send_keys(
            str(os.getenv("UPWORK_USERNAME"))
        )
        driver.find_element(By.ID, "login_password_continue").click()
        time.sleep(1)
        driver.find_element(By.CLASS_NAME, "up-input").send_keys(
            str(os.getenv("UPWORK_PASS"))
        )
        time.sleep(1)
        button = driver.find_element(By.XPATH, '//*[@button-role="continue"]')
        webdriver.ActionChains(driver).move_to_element(button).click(button).perform()

    login()

    for url in urls:
        driver.get(url)
        wait(driver, 5).until(EC.presence_of_element_located)
        # skip if private ad
        webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        try:
            driver.find_elements(By.XPATH, '//div[@data-test="error-visitor"]')
        except NoSuchElementException: pass
        try:
            driver.find_element(By.XPATH, '//div[@data-test="forbidden"]')
            continue
        except NoSuchElementException: pass
        try:
            driver.find_element(
                By.XPATH,
                "//span[contains(@class, 'vertical-align-middle') and contains(text(), 'U.S.')]",
            )
            continue
        except NoSuchElementException: pass
        try:
            client_spent = driver.find_element(By.XPATH, '//*[@data-qa="client-spend"]').text
            match = re.search('\$(\d+(\.\d+)?)(?=\s*K)', client_spent)
            if match:
                amount = match.group(1)
                if float(amount) < 1: continue
        except NoSuchElementException: pass
        try:
            hire_rate = re.search(r'(\d+)% hire rate', driver.find_element(By.XPATH, '//li[@data-qa="client-job-posting-stats"]').text).group(1)
            if float(hire_rate) <= 20: continue
        except NoSuchElementException: pass
        try:
            middle_rate = re.search(r'$(\d+)', driver.find_element(By.XPATH, '//li[@data-qa="client-hourly-rate"]').text).group(1)
            if float(middle_rate) < 20: continue
        except NoSuchElementException: pass
        title = driver.find_element(
            By.XPATH, "//header[@class='up-card-header d-flex']/h1"
        ).text
        # ad_id = re.split("%7E|_~", url)[1].split("?")[0]
        # skills = driver.find_elements(By.XPATH, '//span[@data-test="skill"]')
        # skills_str = ", ".join([i.text for i in skills])
        # description = driver.find_element(
        #     By.XPATH, '//div[@data-test="description"]'
        # ).text.replace("\n", " ")
        # try:
        #     questions = driver.find_elements(By.XPATH, '//div[@data-test="questions"]')
        #     questions_str = ", ".join([i.text for i in questions])
        # except NoSuchElementException:
        #     pass

        text = f"""{title}\n{url}"""
        send_msg(sender, text)
    driver.quit()


def parse_xml(query) -> list[str]:
    skill_query = query.replace(" ", "+")
    feed_url = f"https://www.upwork.com/ab/feed/jobs/rss?q={skill_query}&sort=recency"
    feed = feedparser.parse(feed_url)
    count = 0
    now = pendulum.now("UTC")
    urls = []
    for entry in feed.entries:
        article_desc = entry.description
        link = re.findall('a href="(.+)"', article_desc)[0].strip()
        ad_id = re.split("%7E|_~", link)[1].split("?")[0]
        countries = re.findall("Country<\/b>:(.+)", article_desc)
        country = "".join(countries).replace(" ", "")
        if ad_id in ids:
            continue
        if country in BAD_COUNTRIES:
            continue
        job_dt = pendulum.from_format(
            entry.published, "ddd, DD MMM YYYY HH:mm:ss +0000"
        )
        if job_dt < now - TIME_IN_PAST:
            continue

        if re.search("Budget", article_desc):
            budget_match = re.findall("Budget<\/b>:\s\$(.+)", article_desc)
            if budget_match:
                budget = int(budget_match[0].replace(",", ""))
                if int(budget) < MIN_BUDGET:
                    continue
        elif re.search("Hourly Range", article_desc):
            try:
                _, max_range_value = re.findall(
                    "Hourly Range<\/b>: \$(\d+)\.00-\$(\d+)\.", article_desc
                )[0]
            except IndexError:
                max_range_value = re.findall(
                    "Hourly Range<\/b>: \$(\d+)\.00\n", article_desc
                )[0]
            if int(max_range_value) < MAX_RANGE_FROM:
                continue
        urls.append(link)
        ids.add(ad_id)
        count += 1
    print(f"{now} {skill_query} {TIME_IN_PAST} {count}")
    with open("ad_ids.pkl", 'wb') as f:
        pickle.dump(ids, f)

    return urls


def main():
    for query, sender in SEARCH_QUERIES:
        urls = parse_xml(query)
        if urls:
            parse_with_selenium(urls, sender)
    return print('Run finished')



if __name__ == "__main__":
    main()
