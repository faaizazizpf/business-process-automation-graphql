
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium import webdriver


from get_buxfer_from_sheet import get_all_buxfer_users
from datetime import datetime, timedelta

import schedule
import requests
import logging
import random
import time
import json
import sys
import os



from get_buxfer_from_sheet import *
# UTILITIES==========================================================================
LOGIN_URL="https://www.buxfer.com/login"
USER_ID_FIELD="//input[@name='email']"
PASSWORD_FIELD="//input[@type='password']"
SUBMIT_FIELD="(//A[@loadingmode='default'])[1]"

# CENTER LOW
SYNC_STATUS="//div[contains(@class,'errorsProgressContainer')]"   #INVISIBLE IF NO UNSYNCED ACCOUNT # IF ELEMENT VISIBLE: click SYNC_BTN  
SYNC_BTN="//div[contains(@class,'syncAction')]"
SYNC_STATUS_SYNCED="//div[@class='inputLabel' and text()='Synced']"
SYNC_STATUS_SYNCING="//div[@class='inputLabel' and text()='Syncing']"
# LEFT PANEL
SYNC_ALL="//DIV[@CONTROLLER='UISyncAllButtonController']"   # NOT PRESENT IF NOT UNSYNCED ACCOUNT # IF ELEMENT PRESENT: CLICK OUT_OF_SYNC_ICONS
OUT_OF_SYNC_ICONS="//div[@class='outOfSync']"
OUT_OF_SYNC_TEXT="//div[@class='outOfSync']//ancestor::div[@class='UILeftRight']//div[@class='lF']//div[@class='itemName']"

# =============================Bank Account Logger=========================
import logging
import os

def setup_account_logger():
    logger = logging.getLogger("account_logger")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        # Save in a separate file
        handler = logging.FileHandler("account_status.log")
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

# Initialize once globally
account_logger = setup_account_logger()

# -----------------------Bank Account Logger-----------------------



def setup_python_logging(log_name: str):
    """
    Set up a logger that writes to both terminal and file.
    """
    logger = logging.getLogger(log_name)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:  # prevent duplicate handlers
        formatter = logging.Formatter('%(asctime)s :%(filename)s :%(lineno)d :%(levelname)s:-----%(message)s')

        # Console handler
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        # File handler
        file_handler = logging.FileHandler("buxfer_automation.log")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

# Initialize logger
logger = setup_python_logging(__name__)



class SetChrome:
    def __init__(self, data_dir):
        self.data_dir = f"C:/chromeprofiles_other/{data_dir}"
        logger.info(f"INFO: Setting Chrome for user {data_dir}")




    def get_driver(self, proxy_info=None):
        """
        Set up chrome driver
        :param proxy_info:  Proxy information in the format IP:PORT or HOST:PORT. (String)
        :return:
        """
        chrome_options = webdriver.ChromeOptions()
        # chrome_options.add_argument('--headless')  # <--- This is the key

        chrome_options.add_argument(f"--user-data-dir={self.data_dir}")
        logger.info(f"INFO: Adding experimental options")
        # chrome_options.add_experimental_option('w3c', False)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

        chrome_options.add_argument('--disable-blink-features=AutomationControlled')

        caps = webdriver.DesiredCapabilities.CHROME.copy()
        caps["pageLoadStrategy"] = "none"

        if proxy_info:
            chrome_options.add_argument('--proxy-server=' + proxy_info)

        logger.info("Setting Chrome Options.")
        service = Service()
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_window_size(1600, 2000)
        driver.get("https://www.top10vpn.com/tools/what-is-my-ip/?wimi-preview")
        time.sleep(5)
        return driver

def find_presence_of_element(driver, xpath, time_delay=3.0):
# check_stop_file()
    try:
        element = WebDriverWait(driver, time_delay).until(EC.presence_of_element_located((By.XPATH, xpath)))
        logger.info(f"Element {element} at {xpath}  present")
    except Exception as e:
        # traceback.print_exc()
        logger.info(f"Error finding element given by xpath {xpath}. Details {e}")
        return False

    return True

def get_element_text(driver, xpath, time_delay=3.0):
    # check_stop_file()
    try:
        element = WebDriverWait(driver, time_delay).until(EC.presence_of_element_located((By.XPATH, xpath)))
        element_text = element.text
        logger.info(f"Text found: {element_text}. \n For element {xpath} ")
    except Exception as e:
        # traceback.print_exc()
        logger.info(f"Errorgetting text for the element given by xpath {xpath}. Details {e}")
        script = "return document.getElementById('hidden_div').innerHTML"
        element_text = None

    return element_text
class get_buxfer_accounts:
    def __init__(self, user_id, password, chrome_profile_dir=None, proxy_info=None):
        self.user_id = user_id
        self.password = password
        self.driver = None
        self.chrome_profile_dir = chrome_profile_dir
        self.proxy_info = proxy_info
        self.login_status = False
        self.account_sync_status=''


# -----------------------------LOGGIN BANK ACCOUNT-------------------------
    def log_user_status(self, driver):
        try:
            # Get ALL account blocks (both in-sync and out-of-sync)
            accounts = driver.find_elements(By.XPATH, "//div[@class='UILeftRight']")

            for account in accounts:
                try:
                    bank_name = account.find_element(By.XPATH, ".//div[@class='itemName']").text.strip()
                except NoSuchElementException:
                    continue  # skip if itemName not found

                try:
                    # Check if this account block has outOfSync class inside
                    account.find_element(By.XPATH, ".//div[contains(@class, 'outOfSync')]")
                    sync_status = "Out of Sync"
                except NoSuchElementException:
                    sync_status = "OK"

                account_logger.info(f"user_id: {self.user_id} - Bank: {bank_name} ({sync_status})")
        except Exception as e:
            account_logger.error(f"user_id: {self.user_id} - ❌ Failed to extract bank list: {e}")

    
    def log_out_of_sync_accounts(self, driver):
        try:
            out_of_sync_accounts = driver.find_elements(
                By.XPATH,OUT_OF_SYNC_TEXT
            )

            for element in out_of_sync_accounts:
                bank_name = element.text.strip()
                account_logger.info(f"user_id: {self.user_id} - Bank: {bank_name} (Out of Sync)")

            if not out_of_sync_accounts:
                account_logger.info(f"user_id: {self.user_id} - All banks in sync.")

        except Exception as e:
            account_logger.error(f"user_id: {self.user_id} - ❌ Error finding out-of-sync banks: {e}")

    def set_driver(self):
        if not self.chrome_profile_dir:
            self.chrome_profile_dir = self.user_id
        chrome = SetChrome(self.chrome_profile_dir)

        self.driver = chrome.get_driver(proxy_info=self.proxy_info)

    
    # def sync(self):
    #     hasUnsynced=False

    #     #Added time delay here as the below if statement was skipped without checking after page loading time was high.
    #     count=0
    #     while find_presence_of_element(self.driver, xpath=OUT_OF_SYNC_ICONS,time_delay=30) and count<2:
    #         logger.info(f"%{100}")
    #         logger.info(f"This account is out of sync")
    #         logger.info(f"-"*30)
    #         logger.info(f"Clicking sync center btn")
    #         logger.info(f"%"*100)                                                                                                                                         
    #         # # ==============STOPPER==============
    #         # logger.info(f"STOPPER ON: ")
    #         # logger.info(f"count of icons{ str(len(self.driver.find_elements(By.XPATH, OUT_OF_SYNC_ICONS)))}")
    #         # time.sleep(12160)
    #         # return False
    #         # # ==============STOPPER==============
    #         click_element(self.driver,SYNC_BTN,time_delay=120)
    #         element_SYNC_STATUS_SYNCING=self.driver.find_element(By.XPATH,SYNC_STATUS_SYNCING)
    #         while (element_SYNC_STATUS_SYNCING.is_displayed()):
    #             logger.info(f"(S) "*30)
    #             logger.info(f"Syncing message appeared. Waiting 10 seconds")
    #             logger.info(f"(S) "*30)
    #             time.sleep(10)
    #             element_SYNC_STATUS_SYNCING=self.driver.find_element(By.XPATH,SYNC_STATUS_SYNCING)
    #         count+=1

    #     status_option=["Out of Sync","Login Issue","Sync"]
    #     if len(self.driver.find_elements(By.XPATH, OUT_OF_SYNC_ICONS))>0:
    #         logger.info(f"(I) "*30)
    #         logger.info(f"Failed sync Icons are still showing. Syncing Unsuccessful")
    #         logger.info(f"(I) "*30)
    #         self.account_sync_status=status_option[0]
    #     else:
    #         logger.info(f"[P] "*30)
    #         logger.info(f"All accounts are synced successfully. No Unsync Icon is showing")
    #         logger.info(f"[P] "*30)
    #         self.account_sync_status=status_option[2]
    #     self.log_user_status(self.driver)
    #     self.driver.close()
        

    # def alert_monday(self):
    #     logger.info(f"Sending Monday Alert to the team.")

    #     from monday_sync_updater import MondaySyncUpdater

    #     API_KEY = 'eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjUzMjYzNDMzMCwiYWFpIjoxMSwidWlkIjo3NzQyNjMwNSwiaWFkIjoiMjAyNS0wNi0zMFQwOToyNTozMi4xNTZaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6NjExMjgwNywicmduIjoidXNlMSJ9.FQR1op99guHz9QRLGSk1zFH0SaImEWJtBu-2jAIq_x8'
    #     BOARD_ID = 9415114344

    #     updater = MondaySyncUpdater(api_key=API_KEY, board_id=BOARD_ID)

    #     # Reset the status on monday board first!
    #     if self.account_sync_status!="Login Issue":
    #         updater.update_status(self.user_id, "Login Issue")
    #         time.sleep(3)
    #     updater.update_status(self.user_id, self.account_sync_status)

    #     logger.info(f"Monday Alert Sent")
    # # def get_buxfer_accounts(self):
    # #     pass
    def login_user(self):
        if not self.driver:
            self.set_driver()
            time.sleep(3)
        self.driver.get(LOGIN_URL)
        self.driver.maximize_window()
        enter_user_id = enter_field_value(self.driver, USER_ID_FIELD, self.user_id)
        if enter_user_id is True:
            logger.info(f"User Id entered successfully")
        else:
            logger.error(f"Error Entering user id in field")

        enter_password = enter_field_value(self.driver, PASSWORD_FIELD, self.password)
        if enter_password is True:
            logger.info(f"Password entered successfully")
        else:
            logger.error(f"Error entering password in field")

        enter_submit = click_element(self.driver, SUBMIT_FIELD)
        if enter_submit is True:
            logger.info(f"Submit clicked successfully")
        else:
            logger.error(f"Error clicking submit button")

        time.sleep(5) 

def enter_field_value(driver, xpath, value, time_delay=3.0, pause_after_action=1):
    # check_stop_file()
    try:
        empty_field = WebDriverWait(driver, time_delay).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        sleepTime = time_delay / 2
        time.sleep(sleepTime)
        # -----------------RANDOM DELAY-----------------------
        timedelay=random.uniform(2.50, 5.41)
        time.sleep(timedelay)
        # -----------------RANDOM ACTIVITY-----------------------
        actions = ActionChains(driver)
        # Randomly move mouse to top of the page or some element
        actions.move_by_offset(random.randint(5, 50), random.randint(5, 50)).perform()


        empty_field.click()
        # -----------------RANDOM DELAY-----------------------
        timedelay=random.uniform(1.50, 2.41)
        time.sleep(timedelay)
        # -----------------RANDOM DELAY-----------------------
        empty_field.clear()
        # -----------------RANDOM DELAY-----------------------
        timedelay=random.uniform(1.50, 2.41)
        time.sleep(timedelay)
        # -----------------RANDOM DELAY-----------------------
        empty_field.send_keys(str(value))
        logger.info(f"Entered value into field at {xpath}")
    except Exception as e:
        logger.info(f"First Exception entering value {e}")
        try:
            empty_field = WebDriverWait(driver, time_delay).until(EC.element_to_be_clickable((By.XPATH, xpath)))
            sleepTime = time_delay / 2
            time.sleep(sleepTime)
            empty_field.send_keys(str(value))
            logger.info(f"Entered value into field at {xpath}")
        except Exception as e_:
            # traceback.print_exc()
            logger.info(f"Error entering value for the element given by xpath {xpath}. Details {e_} ")
            return False
    time.sleep(pause_after_action)
    return True



def click_element(driver, xpath, time_delay=3.0, pause_after_action=1, 
                  use_scroll=False, use_js_click=False, wait_for_visible=False):
    try:
        if wait_for_visible:
            WebDriverWait(driver, time_delay).until(EC.visibility_of_element_located((By.XPATH, xpath)))
        element = WebDriverWait(driver, time_delay).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        # --------------RANDOM ACTION---------------
        actions = ActionChains(driver)
        # Randomly move mouse to top of the page or some element
        actions.move_by_offset(random.randint(5, 50), random.randint(5, 50)).perform()
        # ------------------------------------------


        if use_scroll:
            # -----------------RANDOM DELAY-----------------------
            timedelay=random.uniform(1.50, 2.41)
            time.sleep(timedelay)
            # ----------------------------------------------------
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(1)
        if use_js_click:
            # -----------------RANDOM DELAY-----------------------
            timedelay=random.uniform(1.50, 3.41)
            time.sleep(timedelay)
            # ----------------------------------------------------
            driver.execute_script("arguments[0].click();", element)
        else:
            # -----------------RANDOM DELAY-----------------------
            timedelay=random.uniform(1.50, 3.41)
            time.sleep(timedelay)
            # ----------------------------------------------------
            element.click()
        logger.info(f"Element at {xpath}  successfully clicked")
        time.sleep(pause_after_action)

    except Exception as e:
        logger.info(f"Error clicking element given by xpath {xpath}. Details: {e}")
        return False

    return True


# LOGIN





def test_proxy(proxy):  
    TIMEOUT = 3
    IP_ENDPOINTS = [
        ("json", "https://api.ipify.org?format=json",  lambda r: r.json()["ip"]),
        ("json", "https://ipinfo.io/json",             lambda r: r.json()["ip"]),
    ]
    proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
    start   = time.perf_counter()

    for kind, url, extractor in IP_ENDPOINTS:
        try:
            resp = requests.get(url, proxies=proxies, timeout=TIMEOUT, verify=False)
            resp.raise_for_status()
            ext_ip = extractor(resp)
            rtt_ms = (time.perf_counter() - start) * 1000
            msg = f'{proxy} : {ext_ip} - {round(rtt_ms, 1)}'
            logger.info(msg)
            return True
        except Exception:
            continue   
    logger.info(f'{proxy} : Bad')
    return False
 
 

#  ===================MAIN 

def get_working_proxy():
    proxy_list = ["3128", "3129", "3130"]
    base = "100.85.208.254:"
    for _ in range(len(proxy_list)):
        proxy_port = random.choice(proxy_list)
        full_proxy = base + proxy_port
        if test_proxy(full_proxy):
            return full_proxy
        logger.warning(f"Proxy {full_proxy} failed, trying next...")
    return None

def process_account(account):
    email = account["Email"]
    password = account["Password"]
    proxy = get_working_proxy()

    if not proxy:
        logger.error("No working proxy found. Skipping account.")
        return False

    try:
        logger.info(f"Starting sync for {email}")
        user = get_buxfer_accounts(user_id=email, password=password, proxy_info=proxy)
        user.login_status = user.login_user()
        # user.sync()
        # user.log_user_status(user.driver)
        user.log_out_of_sync_accounts(user.driver)
        logger.info(f"Completed log_user_status for {email}")
        return True
    except Exception as e:
        logger.error(f"log_user_status failed for {email}: {e}")
        try:
            fallback = get_buxfer_accounts(user_id=email, password=password, proxy_info=None)
            # fallback.alert_monday("Login Issue")
        except Exception as inner:
            logger.error(f"Failed to log_user_status: {inner}")
        return False

def job_all_accounts():
    accounts = get_all_buxfer_users()
    # accounts=accounts[6:7]
    total = len(accounts)
    success_flags = [False] * total

    logger.info(f"[DAILY RUN] Total accounts to process: {total}")

    # Retry loop until all succeed
    while not all(success_flags):
        for i, account in enumerate(accounts):
            if not success_flags[i]:
                logger.info(f"[{i+1}/{total}] Retrying...")
                success_flags[i] = process_account(account)
        time.sleep(3)  # slight delay between retries

    logger.info("🎉 All accounts synced successfully!")

# Run once immediately
logger.info("Running full account automation now...")
job_all_accounts()

# Get current time + 1 minute
run_time = (datetime.now() + timedelta(minutes=1)).strftime("%H:%M")

print("Scheduling to run daily at:", run_time)


logger.info("Scheduler started for daily automation at 2:00 AM...")
while True:
    schedule.run_pending()
    time.sleep(1)
