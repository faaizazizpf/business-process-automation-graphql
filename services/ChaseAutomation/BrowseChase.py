

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium import webdriver


from datetime import datetime, timedelta
import time
from datetime import datetime
import schedule

import requests
import logging
import random
import time
import sys
import re
LOGIN_URL="https://www.chase.com/?jp_pet=tnt-11070a&"
USER_ID_FIELD="//input[@id='userId-text-input-field']"
PASSWORD_FIELD="//input[@id='password-text-input-field']"
SUBMIT_BUTTON="//button[@id='signin-button']"
print_button="//mds-button[@id='globalToolTip']//following-sibling::button"

def stopper(point="",debug_value=""):
    logger.info("\n\n\n")
    logger.info("========[stopper in session]======== "*3)
    logger.info(f"Reach point {str(point)}\n")
    logger.info(f"{str(debug_value)}")
    input_=input("Do you want to continue? ")
    logger.info("========[stopper ended]======== "*3)
    logger.info("\n\n\n") 


def hover_element(driver,xpath):
    tutorials = driver.find_element(By.XPATH, xpath)
    actions = ActionChains(driver)
    actions.move_to_element(tutorials).perform()
    time.sleep(10)

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

def get_api_root():
    #api_root = f"http://zoesol.mooo.com:7180/zoeapi200130/odata/"
    api_root = f"http://zs300.zoesols.com:7180/zoeapirel2024/odata/"
    return api_root 

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
        file_handler = logging.FileHandler("chase_automation.log")
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
        chrome_options.add_argument('--disable-logging')  # Tries to reduce noise
        chrome_options.add_argument('--log-level=3')      # Only fatal errors
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])  # Remove DevTools noise
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
        # logger.info("self.chrome_profile_dir: ",self.chrome_profile_dir)
        if not self.chrome_profile_dir:
            self.chrome_profile_dir = self.user_id
        chrome = SetChrome(self.chrome_profile_dir)

        self.driver = chrome.get_driver(proxy_info=self.proxy_info)

    
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

        enter_submit = click_element(self.driver, SUBMIT_BUTTON)
        if enter_submit is True:
            logger.info(f"Submit clicked successfully")
        else:
            logger.error(f"Error clicking submit button")

        time.sleep(5)

    def print_statement(self):
        print_submit = click_element(self.driver, print_button)
        if print_submit is True:
            logger.info(f"Submit clicked successfully")
        else:
            logger.error(f"Error clicking submit button")

        time.sleep(5)

    def hover_print(self):
        stopper("hover_print(self):")
        hover_element(self.driver, print_button)



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


import json

# Load credentials from the JSON file
with open('credentials.json', 'r') as f:
    data = json.load(f)

# Loop through each account and print details
accounts = data.get('accounts', [])
for account in accounts:
    email = account.get('email', 'N/A')
    password = account.get('password', 'N/A')
    print(f"email={email}")
    print(f"password={password}")
    proxy = get_working_proxy()
    if not proxy:
        logger.error("No working proxy found. Skipping account.")
    else:
        logger.info(f"Working proxy found for {email}")
        user = get_buxfer_accounts(user_id=email, password=password, proxy_info=proxy)
        user.login_status = user.login_user()
        logger.info(f"Chase Account named: {email} is logged in!")
        user.hover_print()
        user.print_statement()
        time.sleep(999999)
    
