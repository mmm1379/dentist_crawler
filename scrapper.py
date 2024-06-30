import os
import threading
import requests
from bs4 import BeautifulSoup
from queue import Queue, Empty
from threading import Thread
import time

from tqdm import tqdm

from dentist_scrapper import get_doctor_info
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pickle

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name('dentist-scrapper-312bdd3b19c6.json', scope)
gc = gspread.authorize(credentials)
sheet = gc.open("dentists").sheet1

url_queue = Queue()

base_url = "https://doctoreto.com/doctors/speciality/dentist"
d_lock = threading.Lock()

viewed_dentists = set()
viewed_dentists_pkl = 'viewed_dentists.pkl'
viewed_dentists_bar = tqdm(total=None, desc='viewed dentists')
found_urls_bar = tqdm(total=None, desc='found urls')


class Dentist:
    def __init__(self, name, code, specialty, city, profile_url, ):
        self.name = name
        self.code = code
        self.specialty = specialty
        self.city = city
        self.profile_url = profile_url


def scraper_worker():
    page = 1
    """Scrape profile links and add them to the queue"""
    while True:
        page_url = f"{base_url}?page={page}"
        response = requests.get(page_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        add_links_in_suop_to_queue(soup)
        next_page_link = soup.find('a', aria_label="صفحه بعد")
        if not next_page_link:
            print("finished gathering urls")
            break
        page += 1
        found_urls_bar.update(1)
        time.sleep(1)  # Respectful delay to avoid overwhelming the server


def add_links_in_suop_to_queue(soup):
    div = soup.select_one(
        f"html > body > div:first-of-type > div:first-of-type > div > div:first-of-type > div > div:nth-of-type(2) > div > div:nth-of-type(2) > div:nth-of-type(2)")
    links = [a['href'] for a in div.find_all('a', href=True)]
    full_links = [f"https://doctoreto.com{link}" for link in links if link not in viewed_dentists]
    url_queue.queue.extend(full_links)


def processor_worker():
    """Process profile links from the queue and extract details"""
    while True:
        try:
            profile_url = url_queue.get(timeout=30)
            dentist = get_doctor_info(profile_url)
            with d_lock:
                save_dentist(dentist)

        except Empty:
            break


def save_dentist(dentist):
    save_dentist_to_sheet(dentist)
    viewed_dentists.add(dentist['url'])
    viewed_dentists_bar.update(1)


def save_dentist_to_sheet(dentist):
    header = list(dentist.keys())
    if sheet.row_count == 0:
        sheet.insert_row(header, index=1)
    row_data = [str(dentist[key]) for key in header]
    sheet.append_row(row_data)


def start_scraper_worker():
    threads = []
    thread = Thread(target=scraper_worker)
    thread.start()
    threads.append(thread)
    return threads


def start_processor_workers():
    threads = []
    for i in range(20):
        thread = Thread(target=processor_worker)
        thread.start()
        threads.append(thread)
    return threads


def load_viewed_dentists():
    global viewed_dentists
    if os.path.exists(viewed_dentists_pkl):
        with open(viewed_dentists_pkl, 'rb') as file:
            viewed_dentists = pickle.load(file)


def wait_for_threads():
    # Wait for all threads to complete
    for thread in scraper_threads:
        thread.join()
    url_queue.join()  # Wait until all items in the queue are processed
    for thread in processor_threads:
        thread.join()


def save_viewed_dentists():
    with open(viewed_dentists_pkl, 'wb') as file:
        pickle.dump(viewed_dentists, file)


if __name__ == '__main__':
    try:
        load_viewed_dentists()
        scraper_threads = start_scraper_worker()
        processor_threads = start_processor_workers()
        wait_for_threads()
    except Exception as e:
        print(e)
        save_viewed_dentists()
