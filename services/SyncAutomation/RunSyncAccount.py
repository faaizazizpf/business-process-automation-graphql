

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from utils import *

from get_buxfer_from_sheet import get_all_buxfer_users
from datetime import datetime, timedelta
import time
from datetime import datetime
import schedule
import json
import requests
import logging
import random
import time
import sys
import re


from get_buxfer_from_sheet import *

from monday_sync_updater import MondaySyncUpdater

API_KEY = ''
BOARD_ID = 9415114344
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
BUXFER_DASHBOARD="//div[@class='pageTitleContainer navigationCategoryDashboard']"
OUT_OF_SYNC_TEXT="//div[@class='outOfSync']//ancestor::div[@class='UILeftRight']//div[@class='lF']//div[@class='itemName']"


import argparse
parser = argparse.ArgumentParser(description="Run automation scheduler.")


parser.add_argument(
"--mode",
choices=["daily", "now"],
required=True,
help="daily = run daily at fixed time, now = run 1 minute from current time"
) # usage example : python scheduler.py --mode now
parser.add_argument(
"--time",
type=str,
default="08:40",
help="Time in HH:MM format for daily mode (default: 02:00)"
) # usage example :python scheduler.py --mode daily --time 02:30




SCHEDULE_TIME = ""
args = parser.parse_args()
if args.mode == "daily":
    SCHEDULE_TIME = args.time
    print(f"📅 Scheduled to run daily at {SCHEDULE_TIME}")

elif args.mode == "now":
    SCHEDULE_TIME = (datetime.now() + timedelta(minutes=1)).strftime("%H:%M")
    print(f"⏱️ Scheduled to run 1 minute from now at {SCHEDULE_TIME}")




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


def get_api_root():
    #api_root = f"http://zoesol.mooo.com:7180/zoeapi200130/odata/"
    api_root = f"http://zs300.zoesols.com:7180/zoeapirel2024/odata/"
    return api_root

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
        chrome_options.add_argument('--headless')

        chrome_options.add_argument('--disable-logging')  # Tries to reduce noise
        chrome_options.add_argument('--log-level=3')      # Only fatal errors
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])  # Remove DevTools noise

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
        # driver.maximize_window()
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
        logger.info(f"Text found for element at  {xpath}")
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
    def set_driver(self):
        if not self.chrome_profile_dir:
            self.chrome_profile_dir = self.user_id
        chrome = SetChrome(self.chrome_profile_dir)

        self.driver = chrome.get_driver(proxy_info=self.proxy_info)

    def wait_for_sync_to_complete(self):
        # stopper("def wait_for_sync_to_complete(self, timeout=120):")
        driver=self.driver
        retries = 0
        while retries < 2 :
            try:
                click_element(driver, SYNC_BTN, time_delay=120)
                logger.info("Sync button clicked. Checking for syncing status...")
                # Wait for SYNC_STATUS_SYNCING to appear (max 10 sec)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, SYNC_STATUS_SYNCING))
                )
                logger.info(f"[Retry {retries+1}] Syncing message appeared.")

                # Now wait for it to disappear (max 30 sec)
                WebDriverWait(driver, 30).until_not(
                    EC.presence_of_element_located((By.XPATH, SYNC_STATUS_SYNCING))
                )
                logger.info(f"[Retry {retries+1}] Sync completed successfully.")
                break  # Exit loop after success

            except Exception as e:
                logger.warning(f"[Retry {retries+1}] Syncing did not finish in time. Retrying...")
                retries += 1
                time.sleep(2)  # brief pause before retry

        if retries == 2:
            logger.error("2 retries completed ")

        out_of_sync_icons = driver.find_elements(By.XPATH, OUT_OF_SYNC_ICONS)
        # Final status check for sync issues
        if out_of_sync_icons:
            logger.warning(f"{len(out_of_sync_icons)} account(s) still out of sync.")
        else:
            logger.info("All accounts are in sync.")


    def sync(self):
        # stopper("def sync(self):")
        hasUnsynced=False

        #Added time delay here as the below if statement was skipped without checking after page loading time was high.
        count=0

        # stopper(find_presence_of_element(self.driver, xpath=OUT_OF_SYNC_ICONS,time_delay=30))
        if find_presence_of_element(self.driver, xpath=BUXFER_DASHBOARD, time_delay=60) is None:
            self.account_sync_status=status_option[1]
            self.alert_monday()
            self.driver.close()
            return False
        # while (find_presence_of_element(self.driver, xpath=OUT_OF_SYNC_ICONS,time_delay=20) is None) and count<=1: 







        # # out of sync icons is visible and retried less than 2 times
        # while find_presence_of_element(self.driver, xpath=OUT_OF_SYNC_ICONS,time_delay=10) and count<=1:
        #     stopper("find_presence_of_element(self.driver, xpath=OUT_OF_SYNC_ICONS,time_delay=30) and count<=1")

        #     logger.info(f"%{100}")
        #     logger.info(f"This account is out of sync")
        #     logger.info(f"-"*30)
        #     logger.info(f"Clicking sync center btn")
        #     logger.info(f"%"*100)                  
        #     #                                                                                                                        
        #     # # ==============STOPPER==============
        #     # logger.info(f"STOPPER ON: ")
        #     # logger.info(f"count of icons{ str(len(self.driver.find_elements(By.XPATH, OUT_OF_SYNC_ICONS)))}")
        #     # time.sleep(12160)
        #     # return False
        #     # # ==============STOPPER==============
        #     click_element(self.driver,SYNC_BTN,time_delay=120)

        #     #  WAIT WHILE SYNCING IS LOADING IS VISIBLE
        #     # find_presence_of_element(self.driver, xpath=SYNC_STATUS_SYNCING,time_delay=10)
        #     element_SYNC_STATUS_SYNCING = find_presence_of_element(self.driver, xpath=SYNC_STATUS_SYNCING, time_delay=10)
        #     while element_SYNC_STATUS_SYNCING:
        #         logger.info(f"(S) " * 30)
        #         logger.info(f"Syncing message appeared. Waiting 10 seconds")
        #         logger.info(f"(S) " * 30)
        #         # time.sleep(10)
        #         element_SYNC_STATUS_SYNCING = find_presence_of_element(self.driver, xpath=SYNC_STATUS_SYNCING, time_delay=10)

        #         # element_SYNC_STATUS_SYNCING = find_presence_of_element(By.XPATH, SYNC_STATUS_SYNCING)
        #     count+=1

        out_of_sync_icons = self.driver.find_elements(By.XPATH, OUT_OF_SYNC_ICONS)
        if out_of_sync_icons:
            self.wait_for_sync_to_complete()



        status_option=["Out of Sync","Login Issue","Sync"]
        if len(self.driver.find_elements(By.XPATH, OUT_OF_SYNC_ICONS))>0:
            logger.info(f"(I) "*30)
            logger.info(f"Failed sync Icons are still showing. Syncing Unsuccessful")
            logger.info(f"(I) "*30)
            self.account_sync_status=status_option[0]
        else:
            logger.info(f"[P] "*30)
            logger.info(f"All accounts are synced successfully. No Unsync Icon is showing")
            logger.info(f"[P] "*30)
            self.account_sync_status=status_option[2]
        self.alert_monday()
        self.driver.close()
        
    def save_screenshot_in_directory(self):
                # Get current date
        
        formatted_date = datetime.today().strftime('%Y-%m-%d')

        # Get user's Downloads directory dynamically (cross-platform version shown)
        from pathlib import Path
        downloads_folder = str(Path.home() / "Downloads")
        base_dir = os.path.join(downloads_folder, "buxfer_sync_screenshots")

        # Build account folder path
        account_folder = os.path.join(base_dir, formatted_date, self.account_sync_status)
        os.makedirs(account_folder, exist_ok=True)

        # Final screenshot filename
        screenshot_filename = f"{self.user_id}.png"
        screenshot_path = os.path.join(account_folder, screenshot_filename)

        # Take screenshot

        self.driver.save_screenshot(screenshot_path)
        # stopper("319 self.driver.save_screenshot(screenshot_path)")
        logger.info(rf"Screenshot saved at {screenshot_path}")

    
    def get_out_of_sync_accounts(self):
        try:
            out_of_sync_accounts = self.driver.find_elements(
                By.XPATH,OUT_OF_SYNC_TEXT
            )
            if not out_of_sync_accounts:
                logger.info(f"user_id: {self.user_id} - All banks in sync.")
                return []
            
            list_of_accounts=[]
            for element in out_of_sync_accounts:
                bank_name = element.strip()
                # account_logger.info(f"user_id: {self.user_id} - Bank: {bank_name} (Out of Sync)")
                list_of_accounts.append(bank_name)
            return list_of_accounts
        
        except Exception as e:
            logger.error(f"user_id: {self.user_id} - ❌ Error finding out-of-sync banks: {e}")




    import requests

    def notify_discord(self,message, webhook_url):
        data = {
            "content": message
        }
        response = requests.post(webhook_url, json=data)
        if response.status_code == 204:
            print("✅ Discord notification sent successfully")
        else:
            print(f"❌ Failed to send Discord notification: {response.status_code} - {response.text}")

    def alert_monday(self):
        self.save_screenshot_in_directory()
        logger.info(f"Sending Monday Alert to the team.")


        #TESTING AT ALL STATUS FIRST THEN USE AT OUT OF SYNC
        Buxfer_bot_webhook_url = ""

        captain_hook_webhook_url = ""
        
        discord_webhook_url=captain_hook_webhook_url

        updater = MondaySyncUpdater(api_key=API_KEY, board_id=BOARD_ID)
        # stopper("updater = MondaySyncUpdater(api_key=API_KEY, board_id=BOARD_ID)")
        visible_account_names=[]
        if self.account_sync_status=="Out of Sync":
            try:
                from selenium.webdriver.common.action_chains import ActionChains

                out_of_sync_accounts = self.driver.find_elements(By.XPATH, OUT_OF_SYNC_TEXT)
                # visible_account_names = []


                payload=f"Buxfer ID: {self.user_id} : "

                for element in out_of_sync_accounts:
                    # Scroll the element into view
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                    # Optionally wait briefly to allow text to render
                    time.sleep(0.2)
                    bank_name = element.text.strip()
                    if bank_name:  # Only log non-empty entries
                        visible_account_names.append(bank_name)
                        # account_logger.info(f"user_id: {self.user_id} - Bank: {bank_name} (Out of Sync)")
                        payload=payload+f"""\n \tBank: {bank_name} (Out of Sync)"""               
                        




                self.notify_discord(payload,discord_webhook_url)


                for element in visible_account_names:
                    print(element) 
                # stopper("temp.py > 405: for element in visible_account_names:")          
            except Exception as e:
                account_logger.error(f"user_id: {self.user_id} - ❌ Error finding out-of-sync banks: {e}")

        # Reset the status on monday board first!
        if self.account_sync_status!="Login Issue":
            updater.update_status(self.user_id, "Login Issue")
            time.sleep(3)
        else:
            updater.update_status(self.user_id, "Sync")
            time.sleep(3)
        updater.update_status(self.user_id, self.account_sync_status,visible_account_names)

        logger.info(f"Monday Alert Sent")
    # def get_buxfer_accounts(self):
    #     pass
    def login_user(self):
        if not self.driver:
            self.set_driver()
            time.sleep(3)
        self.driver.get(LOGIN_URL)
        # stopper("self.driver.get(LOGIN_URL)")
        # self.driver.maximize_window()

        # SKIP IF WE ARE NOT AT THE LOGIN PAGE
        if find_presence_of_element(self.driver, xpath=USER_ID_FIELD,time_delay=10):

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
            try:
                click_element(self.driver, SUBMIT_FIELD)
            except:

                time.sleep(3)
                click_element(self.driver, SUBMIT_FIELD)
            # stopper("logger.info(f'Waiting for buxfer homepage to complete')")
            logger.info(f"Waiting for buxfer homepage to complete")

            dashboard=WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.XPATH, BUXFER_DASHBOARD))
                )
            # dashboard = self.driver.find_elements(
            #     By.XPATH,BUXFER_DASHBOARD
            # )
            if not dashboard:
                logger.error(f"Unable to login to buxfer. Retrying")
                click_element(self.driver, SUBMIT_FIELD)
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.XPATH, BUXFER_DASHBOARD))
                )
            if dashboard:
                logger.info(f"Logged into Buxfer. Taking screeshot of the dashboard")

                # self.save_screenshot_in_directory()
            # count=0
            # # stopper("count=0 inside  def login_user(self):")
            # while (find_presence_of_element(self.driver, xpath=BUXFER_DASHBOARD,time_delay=20) is None) and count<=1: 
                
            #     enter_submit = click_element(self.driver, SUBMIT_FIELD)
            #     count+=1

            # if enter_submit is True:
            #     logger.info(f"Submit clicked successfully")
            # else:
            #     logger.error(f"Error clicking submit button")
        
        else:
            logger.info(f"Login form not found. Skipping login")
            
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

def get_mobile_proxy_list(mobilenetwork = None, active_only=False, external=False):
    if active_only:
        proxy_url_end_point = f"{get_api_root()}ZoeProxyServers?$expand=ZoeProxyServerStatus&$filter=ZoeProxyServerStatusId eq 1 and ProxyType eq 'Mobile'"        
    else:
        # DEFAULT URL TO USE
        proxy_url_end_point = f"{get_api_root()}ZoeProxyServers?$expand=ZoeProxyServerStatus&$filter=ProxyType eq 'Mobile'"

    if external:
        proxy_url_end_point = proxy_url_end_point.replace('Mobile', 'External')

    if mobilenetwork:
        proxy_url_end_point = proxy_url_end_point + f" and contains(tolower(ProxyServer), '{mobilenetwork.lower()}')"

    proxy_url_end_point = proxy_url_end_point + f"&$orderby=ProxyServerIPAddress,ProxyServerPort"

    site_response = requests.get(proxy_url_end_point, timeout=8)

    data = site_response.json()
    results = data['value']

    try:
        additional_responses_link = data['@odata.nextLink']
       
    except:
        additional_responses_link = None

    while additional_responses_link is not None:
        suffix_for_next_results_regex = re.compile(r"skip=(\d+)")
        suffix_for_next_results = suffix_for_next_results_regex.search(additional_responses_link).group(1).strip()
        additional_responses_link = f"{proxy_url_end_point}&$skip={suffix_for_next_results}"

        additional_gc_code_site_response = requests.get(additional_responses_link, timeout=8)
        additional_data = additional_gc_code_site_response.json()

        results = results + additional_data['value']

        try:
            additional_responses_link = additional_data['@odata.nextLink']
            suffix_for_next_results_regex = re.compile(r"skip=(\d+)")
            suffix_for_next_results = suffix_for_next_results_regex.search(additional_responses_link).group(1).strip()
            additional_responses_link = f"{proxy_url_end_point}&$skip={suffix_for_next_results}"
           
        except KeyError:
           
            additional_responses_link = None

    return results


def get_working_proxy():
    proxy_list =  get_mobile_proxy_list(active_only=True, external=True)
    proxy_status = False

    for i in range(len(proxy_list)):
    
        proxy_setting = random.choice(proxy_list)
        proxy = f"{proxy_setting['ProxyServerIPAddress']}:{proxy_setting['ProxyServerPort']}"
        proxy_status = test_proxy(proxy)
        
        if proxy_status:
            return proxy

    if not proxy_status:

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
        user.sync()
        logger.info(f"Completed sync for {email}")
        return True
    except Exception as e:
        logger.error(f"Sync failed for {email}: {e}")
        try:
            fallback = get_buxfer_accounts(user_id=email, password=password, proxy_info=None)
            fallback.account_sync_status="Login Issue"
            fallback.alert_monday()
        except Exception as inner:
            logger.error(f"Failed to alert Monday.com: {inner}")
            # stopper("logger.error(f'Failed to alert Monday.com:")
    return False
import time
from datetime import datetime
import schedule

def job_all_accounts():
    accounts = get_all_buxfer_users()
    accounts=accounts[2:6]
    total = len(accounts)
    success_flags = [False] * total
    retry_counts = [0] * total
    retry_counts = [0] * total
    MAX_RETRIES = 3

    logger.info(f"[Daily RUN] Total accounts to process: {total}")

    while not all(success_flags):
        for i, account in enumerate(accounts):
            if success_flags[i]:
                continue
                continue

            if retry_counts[i] >= MAX_RETRIES:
                logger.warning(f"[{i+1}/{total}] Max retries reached. Skipping account: {account['Email']}")
                success_flags[i] = True
                continue

            logger.info(f"[{i+1}/{total}] Attempt {retry_counts[i] + 1}...")
            success = process_account(account)
            if success:
                success_flags[i] = True
            else:
                retry_counts[i] += 1

        time.sleep(3)

    logger.info("🎉 All accounts synced (or skipped after max retries).")
    print("✅ Daily automation complete\n")

# Optional: Run once immediately
# job_all_accounts()
# Optional: Run once immediately
# job_all_accounts()

# # Schedule the job at a fixed daily time (e.g., 03:00 AM)

schedule.every().day.at(SCHEDULE_TIME).do(job_all_accounts)
logger.info(f"Scheduler started for daily automation at {SCHEDULE_TIME}...")

# Keep checking
while True:
    schedule.run_pending()
    time.sleep(60)  # No need to check every second