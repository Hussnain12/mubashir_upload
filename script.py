from datetime import datetime
import csv
import requests
from datetime import datetime, timedelta
from selenium import webdriver as wd
import time
from selenium.webdriver.common.by import By
import pandas as pd
from selenium.webdriver.chrome.options import Options
path = 'chromedriver'

options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')  # Last I checked this was necessary.
driver = wd.Chrome(path, chrome_options=options)

url1 = "https://upgraded.se/konsultuppdrag"
driver.get(url1)

driver.implicitly_wait(5)

click_cancel = driver.find_element(
    By.XPATH, '//*[@id="PopupSignupForm_0"]/div[2]/div[1]').click()
driver.execute_script("window.scrollBy(0, 1000)")
frame1 = driver.find_element(By.ID, 'workbuster_iframe')
driver.switch_to.frame(frame1)
try:
    click_see_more = driver.find_element(
        By.XPATH, '//*[@id="read-more"]').click()
except:
    print("element not found")

# to get all the a tags from the site


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


# airtable_fun(filename="site1.csv")# change after everything is done bro


def get_links():
    get_all_links = driver.find_elements(By.TAG_NAME, "a")
    links_to_jobs_list = []
    for i in get_all_links:
        links_to_jobs_list.append(i.get_attribute("href"))
    return links_to_jobs_list


def get_unmatch_data(new_src, links):
    unmatched = []
    for element in links:
        if element not in new_src:
            unmatched.append(element)
    return unmatched


def get_jobs(unmatched):
    jobs = []
    get_jobs = driver.find_elements(By.XPATH, '//*[@id="items"]/a/div/div[1]')
    count = 0
    for i in get_jobs:
        if len(unmatched) == count:
            break
        jobs.append(i.text)
        count += 1
    return jobs


def get_job_location(unmatched):
    getting_job_location = driver.find_elements(
        By.XPATH, '//*[@id="items"]/a/div/div[3]/div[2]/span')
    job_location_list = []
    count = 0
    for i in getting_job_location:
        if len(unmatched) == count:
            break
        job_location_list.append(i.text)
        count += 1
    return job_location_list


def get_deadline(unmatched):
    get_dead_line = driver.find_elements(
        By.XPATH, '//*[@id="items"]/a/div/div[2]/span')
    dead_line_list = []
    count = 0
    for i in get_dead_line:
        if len(unmatched) == count:
            break
        dead_line_list.append(i.text)
        count += 1
    return dead_line_list


def add_30_days(deadline):

    # Loop through the dates in the list and add 30 days to each date
    for i in range(len(deadline)):
        # Convert the date string to a datetime object
        date_obj = datetime.strptime(deadline[i], '%Y-%m-%d')
        # Add 30 days to the date using timedelta
        new_date = date_obj + timedelta(days=30)
        # Convert the new date back to a string and replace the old date in the list
        deadline[i] = new_date.strftime('%Y-%m-%d')

    # Print the updated list of dates
    return deadline


# getting links from the csv file
links_to_jobs_list = get_links()
df_old = pd.read_csv("site1.csv")
new_src = df_old["Link"].tolist()
# getting unmatched list based on this will get new data to add in the airtable
unmatched = get_unmatch_data(links_to_jobs_list, new_src)
# getting jobs name list
jobs = get_jobs(unmatched)
job_location_list = get_job_location(unmatched)
dead_line_list = get_deadline(unmatched)
dead_line_list = add_30_days(dead_line_list)

sweden_list = ["Sweden"]*len(jobs)

description_list = ["igonre dates"]*len(jobs)

df = pd.DataFrame({"Job_Name": jobs, "Link": unmatched, "Job_Location": job_location_list,
                  "Dead_Line": dead_line_list, "status": sweden_list, "Description": description_list})

# df = pd.DataFrame({"Job_Name": jobs, "Link": unmatched,
#                   "Job_Location": job_location_list, "Dead_Line": dead_line_list})

df.to_csv("site1.csv", mode="a", index=False, header=False)
df.to_csv("to_upload_site1.csv", index=False)
airtable_fun(filename="to_upload_site1.csv")

driver.quit()
