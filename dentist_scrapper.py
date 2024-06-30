from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


def find_element_containing_text(driver, text):
    try:
        # Wait until the element containing the text is present
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{text}')]"))
        )
        return element
    except KeyboardInterrupt:
        raise
    except Exception as e:
        print(f"Error finding element containing text '{text}': {e}")
        return None

def extract_phone_numbers(driver):
    phone_numbers = []
    try:
        spans = get_phone_number_spans(driver)
        for span in spans:
            span.click()
            time.sleep(0.1)  # Wait for the number to be revealed
            phone_numbers.append(span.text)
    except KeyboardInterrupt:
        raise
    except Exception as e:
        print(f"Error extracting phone numbers: {e}")
    return phone_numbers


def get_phone_number_spans(driver):
    phone_span = find_element_containing_text(driver, "تلفن:")
    phone_section = phone_span.find_element(By.XPATH, 'following-sibling::*')
    spans = phone_section.find_elements(By.TAG_NAME, 'span')
    return spans


# Function to extract comments
def extract_comments(driver):
    comments = []
    try:
        # Locate the reviews section
        review_section = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, 'doctor_reactions'))
        )

        while True:
            click_on_load_more_comments_if_possible(review_section)
            try:
                while True:
                    get_comment_on_review_section(comments, review_section)

                    try:
                        click_on_additional_comments_if_present(review_section)
                    except:
                        next_time = review_section.find_element(By.XPATH,"/html/body/div[9]/div/div/div[3]/div[1]/a")
                        if next_time:
                            next_time.click()
                            continue
                        else:
                            break
            except KeyboardInterrupt:
                raise
            except Exception:
                break
    except KeyboardInterrupt:
        raise
    except Exception as e:
        print(f"Error extracting comments: {e}")
    return comments


def click_on_load_more_comments_if_possible(review_section):
    try:
        load_more_button = review_section.find_element(By.XPATH, '//*[@id="doctor_reactions"]/div[3]/div/div[2]/button')
        load_more_button.click()
        time.sleep(1)  # Wait for the new content to load
    except KeyboardInterrupt:
        raise
    except Exception:
        pass


def click_on_additional_comments_if_present(review_section):
    additional_list = review_section.find_element(By.XPATH, '//*[@id="doctor_reactions"]/div[3]/ul')
    if additional_list:
        last_li = additional_list.find_elements(By.TAG_NAME, 'li')[-1]
        last_li.find_element(By.TAG_NAME, 'svg').click()
        time.sleep(2)  # Wait for the new content to load


def get_comment_on_review_section(comments, review_section):
    comment_divs = review_section.find_element(By.XPATH, './/div[3]/div').find_elements(By.XPATH, './div')
    for comment_div in comment_divs:
        # comment = comment_div.find_element(By.XPATH, './div[last()]').text
        ct = comment_div.text
        comments.append(ct.replace("کاربر دکترتو", "بی‌نام"))


def get_doctor_info(url):
    driver = get_driver()
    driver.get(url)

    dentist = get_dentist_info_from_driver(driver, url)
    driver.quit()

    # Output results
    return dentist


def get_dentist_info_from_driver(driver, url):
    code_element = find_element_containing_text(driver, "کد نظام پزشکی")
    code = code_element.text.replace("کد نظام پزشکی:", "") if code_element else "N/A"

    info_root = code_element.find_element(By.XPATH, 'ancestor::div[2]')

    star = code_element.find_element(By.XPATH, '../../../../div[2]/div[1]/div[1]/div[1]').text.split()[0]

    name_element = info_root.find_element(By.XPATH, './/div[1]/h1')
    name = name_element.text if name_element else "N/A"

    specialty_links = info_root.find_element(By.XPATH, './/div[4]')
    specialty = specialty_links.text

    city_element = info_root.find_element(By.XPATH, './/div[2]/a')
    city = city_element.text if city_element else "N/A"

    address_span = find_element_containing_text(driver, "آدرس:")
    address_section = address_span.find_element(By.XPATH, '..')
    address = address_section.text.replace("آدرس:", "")

    phone_numbers = extract_phone_numbers(driver)

    comments = '_________________'.join(extract_comments(driver))

    dentist = {'name': name, 'code': code, 'specialty': specialty, 'city': city, 'address': address, 'url': url,
               'phone_numbers': phone_numbers, 'comments': comments, 'star': star}
    return dentist


def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run Chrome in headless mode (no GUI)
    options.add_argument('--no-sandbox')  # Bypass OS security model
    options.add_argument('--disable-gpu')  # Disable GPU acceleration
    # Initialize the WebDriver with configured options
    driver = webdriver.Chrome(options=options)
    return driver
