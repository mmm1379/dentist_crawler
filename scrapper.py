import threading
import requests
from bs4 import BeautifulSoup
from queue import Queue, Empty
from threading import Thread
import time
from dentist_scrapper import get_doctor_info
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pickle

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

# Path to the downloaded JSON key file from the Google Cloud Console
credentials = ServiceAccountCredentials.from_json_keyfile_name('dentist-scrapper-312bdd3b19c6.json', scope)

# Authenticate with Google Sheets
gc = gspread.authorize(credentials)
sheet = gc.open("dentists").sheet1

# Initialize the VADER sentiment analyzer
# Shared queue for storing profile URLs
url_queue = Queue()

# URL to start scraping from
base_url = "https://doctoreto.com/doctors/speciality/dentist"
viewed_dentists = set()
d_lock = threading.Lock()


class Dentist:
    def __init__(self, name, code, specialty, city, profile_url, ):
        self.name = name
        self.code = code
        self.specialty = specialty
        self.city = city
        self.profile_url = profile_url


def scraper_worker(start_page=1, end_page=1000):
    """Scrape profile links and add them to the queue"""
    for page in range(start_page, end_page + 1):
        page_url = f"{base_url}?page={page}"
        response = requests.get(page_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Locate the profile link elements
        div = soup.select_one(
            f"html > body > div:first-of-type > div:first-of-type > div > div:first-of-type > div > div:nth-of-type(2) > div > div:nth-of-type(2) > div:nth-of-type(2)")
        links = [a['href'] for a in div.find_all('a', href=True)]
        full_links = [f"https://doctoreto.com{link}" for link in links if link not in viewed_dentists]

        # full_link = f"https://doctoreto.com{links[0]}"
        url_queue.queue.extend(full_links)

        time.sleep(1)  # Respectful delay to avoid overwhelming the server


def processor_worker():
    """Process profile links from the queue and extract details"""
    while True:
        try:
            profile_url = url_queue.get(timeout=30)  # Timeout to exit the loop if the queue is empty
            # response = requests.get(profile_url)
            dentist = get_doctor_info(profile_url)
            # Append the dentist's data to a file
            with d_lock:
                header = list(dentist.keys())
                if sheet.row_count == 0:
                    sheet.insert_row(header, index=1)
                row_data = [str(dentist[key]) for key in header]
                sheet.append_row(row_data)
                viewed_dentists.add(dentist['url'])

        except Empty:
            break


if __name__ == '__main__':
    try:
        with open('viewed_dentists.pkl', 'rb') as file:
            viewed_dentists = pickle.load(file)

        # Initialize and start scraper workers
        scraper_threads = []
        for i in range(1):  # Adjust the number of scraper threads as needed
            thread = Thread(target=scraper_worker, args=(1, 10))  # Adjust the page range as needed
            thread.start()
            scraper_threads.append(thread)

        # Initialize and start processor workers
        processor_threads = []
        for i in range(20):  # Adjust the number of processor threads as needed
            thread = Thread(target=processor_worker)
            thread.start()
            processor_threads.append(thread)

        # Wait for all threads to complete
        for thread in scraper_threads:
            thread.join()

        url_queue.join()  # Wait until all items in the queue are processed

        for thread in processor_threads:
            thread.join()
    except Exception as e:
        print(e)
        # Save the set to a file
        with open('viewed_dentists.pkl', 'wb') as file:
            pickle.dump(viewed_dentists, file)
