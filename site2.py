import datetime
from selenium import webdriver as wd
import time
from selenium.webdriver.common.by import By
import re
import pandas as pd
from selenium.webdriver.chrome.options import Options
path = "chromedriver"
options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')  # Last I checked this was necessary.
driver = wd.Chrome(path, chrome_options=options)
import csv

url1 = "https://www.nikita.se/lediga-uppdrag/"
driver.get(url1)
driver.implicitly_wait(2)


def airtable_fun(filename):
    # Set up API credentials and base information
    pat = 'patMBPtmPuuLjfkfi.5484dfcfa7d2baff2bde88f8c9b0e7ac0e535ec09a8a0f9aa8021043090ecd50'
    base_id = "appWFSx6BGg1FmqQh"
    table_name = "URGENT today"

    # Set up API endpoint and headers
    url = f'https://api.airtable.com/v0/{base_id}/{table_name}'
    headers = {
        'Authorization': f'Bearer {pat}',
        'Content-Type': 'application/json'
    }

    # Read in CSV data and convert to list of dictionaries
    with open(filename, 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        data = [row for row in csv_reader]

    # Send POST request to Airtable API to create new records
    for row in data:
        job_name = row['Job_Name']
        links = row['Link']
        location = row['Job_Location']
        # Parse date string into datetime object
        expiry_date = row['Dead_Line']
        status = row['status']
        description = row['Description']
        response = requests.post(url, headers=headers, json={
            'fields': {
                'Job name': job_name,
                'Link': links,
                'Location': location,
                'expired date': expiry_date,
                'status': status,
                'Description': description
            },
            # Converts field values to the appropriate type
            'typecast': True
            # 'position': 'top'  # Adds the new record to the top of the table
        })

        # Print response status code and content
        print(response.status_code)
        print(response.content)


# it will get all the links
get_all_links = driver.find_elements(
    By.XPATH, '//*[@id="open-positions-target"]/ul/li/a')
# saving links in a list to parse it
links = []
for i in get_all_links:
    links.append(i.get_attribute("href"))


df_old = pd.read_csv("site2.csv")
new_src = df_old["Link"].tolist()
unmatched = []
for element in links:
    if element not in new_src:
        unmatched.append(element)

count = 0
get_job_name = driver.find_elements(
    By.XPATH, '//*[@id="open-positions-target"]/ul/li/a/span[2]')
jobs_list = []
for i in get_job_name:
    if count == len(unmatched):
        break
    jobs_list.append(i.text)
    count += 1

paragraphs = []
for i in unmatched:
    # for i in links:
    driver.get(i)
    driver.implicitly_wait(2)
    try:
        find_paragraph = driver.find_element(
            By.XPATH, '/html/body/div[2]/div/section/div[2]/div[1]')
    except:
        find_paragraph = driver.find_element(
            By.XPATH, '/html/body/div[1]/div/section/div[2]/div[1]')
    paragraphs.append(find_paragraph.text)

locations = []

for text in paragraphs:
    if "remote" in text:
        locations.append("remote")
    else:
        match = re.search(
            r'(Location|Ort\.?|Placement|Placering):?\s*(.*)', text)
        if match:
            location_text = match.group(2)
            cities = re.findall(
                r'\b[A-Z][a-z]+(?: [A-Z][a-z]+)?\b', location_text)
            locations.extend(cities)
        else:
            locations.append("remote")


# Get today's date
today = datetime.date.today()

# Add 30 days to today's date
thirty_days_from_today = today + datetime.timedelta(days=30)

# Create a list of dates
date = [thirty_days_from_today.strftime('%Y-%m-%d')] * len(jobs_list)


locations = locations[0:len(jobs_list)]

sweden_list = ["Sweden"]*len(jobs_list)

description_list = ["igonre dates"]*len(jobs_list)


df = pd.DataFrame({"Job_Name": jobs_list, "Link": unmatched, "Job_Location": locations,
                  "Dead_Line": date, "status": sweden_list, "Description": description_list})

df.to_csv("site2.csv", mode="a", index=False, header=False)

df.to_csv("to_upload_site2.csv", index=False)

airtable_fun(filename="to_upload_site2.csv")

driver.quit()
