
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium import webdriver

import requests
import logging
import random
import time
import sys


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

def setup_python_logging(log_name: str):
    """
    Does all the setup for python logging so that it does not have to be done in each file
    :return:
    """
    # Create a logger and set the logging level
    logger = logging.getLogger(log_name)
    logger.setLevel(logging.DEBUG)

    # Create a formatter for the output. The formatter is not added to the logger directly, but the "handler" that the logger will use
    o_formatter = logging.Formatter('%(asctime)s :%(filename)s :%(lineno)d :%(levelname)s:-----%(message)s')

    # handler - stream
    stream_handler = logging.StreamHandler(stream=sys.stdout)
    stream_handler.setFormatter(o_formatter)
    logger.addHandler(stream_handler)

    # Handler - File
    # file_handler = logging.FileHandler("TestFile_ThreadingDemo.log")
    # file_handler.setFormatter(o_formatter)
    # logger.addHandler(file_handler)

    return logger


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ AUTOMATION UTILITY FUNCTIONS
logger = setup_python_logging(__file__)



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
        logger.info(f"Text found for element at  {xpath}")
    except Exception as e:
        # traceback.print_exc()
        logger.info(f"Errorgetting text for the element given by xpath {xpath}. Details {e}")
        script = "return document.getElementById('hidden_div').innerHTML"
        element_text = None

    return element_text
class AmexCardUser:
    def __init__(self, user_id, password, chrome_profile_dir=None, proxy_info=None):
        self.user_id = user_id
        self.password = password
        self.list_of_user_cards_objects = []
        self.list_of_amex_offers = []
        self.list_of_amex_profile = []
        self.list_of_amex_alert_settings = []
        self.list_of_amex_rewards=[]
        self.driver = None
        self.number_of_cards = None
        self.chrome_profile_dir = chrome_profile_dir
        self.proxy_info = proxy_info
        self.login_status = False
        self.account_sync_status=''
    def set_driver(self):
        if not self.chrome_profile_dir:
            self.chrome_profile_dir = self.user_id
        chrome = SetChrome(self.chrome_profile_dir)

        self.driver = chrome.get_driver(proxy_info=self.proxy_info)

    
    def sync(self):
        hasUnsynced=False

        #Added time delay here as the below if statement was skipped without checking after page loading time was high.
        count=0
        while find_presence_of_element(self.driver, xpath=OUT_OF_SYNC_ICONS,time_delay=30) or count<2:
            logger.info(f"%{100}")
            logger.info(f"This account is out of sync")
            logger.info(f"-"*30)
            logger.info(f"Clicking sync center btn")
            logger.info(f"%"*100)                                                                                                                                         
            # # ==============STOPPER==============
            # logger.info(f"STOPPER ON: ")
            # logger.info(f"count of icons{ str(len(self.driver.find_elements(By.XPATH, OUT_OF_SYNC_ICONS)))}")
            # time.sleep(12160)
            # return False
            # # ==============STOPPER==============
            click_element(self.driver,SYNC_BTN,time_delay=120)
            element_SYNC_STATUS_SYNCING=self.driver.find_element(By.XPATH,SYNC_STATUS_SYNCING)
            while (element_SYNC_STATUS_SYNCING.is_displayed()):
                logger.info(f"(S) "*30)
                logger.info(f"Syncing message appeared. Waiting 10 seconds")
                logger.info(f"(S) "*30)
                time.sleep(10)
                element_SYNC_STATUS_SYNCING=self.driver.find_element(By.XPATH,SYNC_STATUS_SYNCING)
            count+=1

        # # ======================== Verify by message ======================

        # sync_status=get_element_text(self.driver,SYNC_STATUS)
        # logger.info(f"Found Text for sync_status: {sync_status}")

        # time.sleep(1169)
        # if sync_status.lower().strip()=="failed":
        #     hasUnsynced=True
        #     logger.info(f"(F) "*30)
        #     logger.info(f"Failed sync status is still showing")
        #     logger.info(f"-"*30)
        #     logger.info(f"Clicking sync all left btn")
        #     logger.info(f"(F) "*30)

        #     # # ==============STOPPER==============
        #     # logger.info(f"STOPPER ON: ")
        #     # time.sleep(60)
        #     # return False
        #     # # ==============STOPPER==============
            
        #     click_element(self.driver,SYNC_ALL,time_delay=120)
            
        #     # #========= tempary fix. Change with logic to wait until syncing in progress is visible
        #     # time.sleep(120)
        #     # # ======================================================================================
    

        # element_SYNC_STATUS_SYNCING=self.driver.find_element(By.XPATH,SYNC_STATUS_SYNCING)
        # while (element_SYNC_STATUS_SYNCING.is_displayed()):
        #     logger.info(f"(S) "*30)
        #     logger.info(f"Syncing message appeared. Waiting 10 seconds")
        #     logger.info(f"(S) "*30)
        #     time.sleep(10)
        #     element_SYNC_STATUS_SYNCING=self.driver.find_element(By.XPATH,SYNC_STATUS_SYNCING)
        # # ======================== Verify by message ======================

        
        # # ---------------------
        # # Display failed text after 2 sync attempts
        # # ----------------------
        # logger.info("&"*100)
        # logger.info(f"Re Checking unsynced accounts after 2 sync attempts")
        # logger.info(f"-"*30)
        # logger.info(f"Looking for 1 failed sync text")
        # syn_status_text=get_element_text(self.driver,SYNC_STATUS)
        # if syn_status_text=="Failed":
        #     logger.info(f"-"*30)
        #     logger.info(f"showing {syn_status_text} text")
        #     logger.info(f"*"*100)

        # # -----------------------
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
        

    def alert_monday(self):
        logger.info(f"Sending Monday Alert to the team: need human intervention")

        from monday_sync_updater import MondaySyncUpdater

        API_KEY = ''
        BOARD_ID = 1

        updater = MondaySyncUpdater(api_key=API_KEY, board_id=BOARD_ID)

        # Update examples
        updater.update_status(self.user_id, self.account_sync_status)
        # updater.update_status("eddieleezoe@gmail.com", "Login Issue")
        # updater.update_status("allenwccman@gmail.com", "Sync")
        # updater.update_status("markccman@gmail.com", "")  # Clear status


        logger.info(f"Monday Alert Sent")
    # def get_buxfer_accounts(self):
    #     pass
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
        # ("text", "https://icanhazip.com",              lambda r: r.text.strip()),
        # ("text", "https://checkip.amazonaws.com",      lambda r: r.text.strip()),
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

    # ================================================Run main
from get_buxfer_from_sheet import get_all_buxfer_users
cron_start=0
cron_end=5
def job():
    accounts=get_all_buxfer_users()
    total_accounts=len(accounts)
    global cron_start,cron_end
    if cron_end>total_accounts:
        cron_start=0
        cron_end=5
    

    for i in range(cron_start,cron_end):
        logger.info(f"Total Accounts: {total_accounts}")
        logger.info(f"[A] "*30)
        logger.info(f"Sync automation started for Sheet Account Number {str(i+2)}. Name: {accounts[i]["Email"]}")
        account=accounts[i]["Email"]
        password=accounts[i]["Password"]
        # account="allenwccman@gmail.com"
        # password="Allenbxf126!"
        proxy_list_1=["3128","3129","3130"]
        Initial_proxy="100.85.208.254:"
        for i in range(len(proxy_list_1)):
            proxy_index=random.randint(0,len(proxy_list_1)-1)
            STATIC_PROXY=Initial_proxy+proxy_list_1[proxy_index]
            # STATIC_PROXY = "24.44.169.104:43003"  # Replace with your actual proxy

        # Test the static proxy (optional)
            proxy_status = test_proxy(STATIC_PROXY)
            logger.info("proxy_status: "+str(proxy_status))
            #DEBUGGER
            # time.sleep(3)
            if proxy_status:
                break
        if proxy_status:
            cards_summary_getter = AmexCardUser(user_id=account, password=password, proxy_info=STATIC_PROXY)
            cards_summary_getter.login_status = cards_summary_getter.login_user()
            cards_summary_getter.sync()
        else:
            logger.error(f"Static proxy {STATIC_PROXY} failed connectivity test")
            # return []
    cron_start+=5
    cron_end+=5
        # ================================================Run main
import schedule
import time
logger.info("[R] "*30)
logger.info("Running once without scheduler to skip waiting first run")
logger.info("[R] "*30)
job()
logger.info("[C] "*30)
logger.info("First Job Complete! Cron has Started!")
logger.info("[C] "*30)
schedule.every().hour.do(job)
while(1):
    schedule.run_pending()