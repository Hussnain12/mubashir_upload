import datetime
from selenium import webdriver as wd
import time
from selenium.webdriver.common.by import By
import re
import pandas as pd
import csv
from selenium.webdriver.chrome.options import Options
path = "chromedriver"
options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')  # Last I checked this was necessary.
driver = wd.Chrome(path, chrome_options=options)
url = 'https://www.nikita.se/ramavtal/'
driver.get(url)
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
    By.XPATH, '//*[@id="ramavtal-target"]/ul/li/a')

# saving the links in a separate list so in next step i can iterate it over and get the location
links_to_jobs = []
for i in get_all_links:
    links_to_jobs.append(i.get_attribute("href"))

df_old = pd.read_csv("data.csv")
new_src = df_old["Links"].tolist()
unmatched = []
for element in links_to_jobs:
    if element not in new_src:
        unmatched.append(element)

# it will get all the job names from the site
count = 0
get_job_name = driver.find_elements(
    By.XPATH, '//*[@id="ramavtal-target"]/ul/li/a/span[2]')
job_name_list = []
for i in get_job_name:
    if count==len(unmatched):
        break
    job_name_list.append(i.text)
    count+=1
    

# saving the data from a page in the paragraph
paragraph = []
for i in unmatched:
# for i in links_to_jobs:
    driver.get(i)
    driver.implicitly_wait(2)
    try:
        find_paragraph = driver.find_element(
            By.XPATH, '/html/body/div[1]/div/section/div[2]/div[1]')
    except:
        find_paragraph = driver.find_element(
            By.XPATH, '/html/body/div[2]/div/section/div[2]/div[1]')
    paragraph.append(find_paragraph.text)


# extracting locations from the paragraph
locations = []
for text in paragraph:
    if "Location:" in text:
        location = text.split("Location:")[1].split("\n")[0].strip()
        locations.append(location)
    else:
        locations.append('remote')


# Get today's date
today = datetime.date.today()

# Add 30 days to today's date
thirty_days_from_today = today + datetime.timedelta(days=30)

# Create a list of dates
date = [thirty_days_from_today.strftime('%Y-%m-%d')] * len(job_name_list)

locations=locations[0:len(job_name_list)]

sweden_list=["Sweden"]*len(job_name_list)

description_list=["igonre dates"]*len(job_name_list)

df = pd.DataFrame({"Job_Name": job_name_list, "Link": unmatched, "Job_Location": locations,
                  "Dead_Line": date, "status": sweden_list, "Description": description_list})


df.to_csv("site3.csv", mode='a', index=False, header=False)
df.to_csv('to_upload_site3.csv', index=False)


airtable_fun(filename="to_upload_site3.csv")

driver.quit()
