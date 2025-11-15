import os
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler
from googleapiclient.discovery import build
from google.oauth2 import service_account
from services.buxfer_service import export_all_transactions_to_drive, save_buxfer_data, get_proxies

load_dotenv()

scheduler = BlockingScheduler()

def schedule_jobs():
    """ Dynamically schedule jobs based on spreadsheet values """
    print("Loading scheduled times from spreadsheet...")

    proxy_list = get_proxies()

    try:
        service = build('sheets', 'v4', credentials=service_account.Credentials.from_service_account_file('credentials.json', scopes=['https://www.googleapis.com/auth/spreadsheets']))
        spreadsheet_id = os.getenv('SPREADSHEET_ID')
        range_name = 'BUXFER ACCOUNTS!A:H'

        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
        values = result.get('values', [])[1:]  # Skip header
        scheduler.add_job(
            export_all_transactions_to_drive,
            'cron',
            hour=9,
            minute=0
        )
        for user in values:
            user_name = user[1]
            scheduled_time = user[6]  # Format should be "HH:MM"
            hour = int(scheduled_time.split(":")[0])
            minute = int(scheduled_time.split(":")[1])

            scheduler.add_job(
                save_buxfer_data,
                'cron',
                hour=hour,
                minute=minute,
                args=[user_name]
            )
            print(f"Scheduled job for {user_name} at {scheduled_time}")

    except Exception as e:
        print("Error scheduling jobs:", e)

schedule_jobs()

print("Scheduler started with dynamic time-based execution using rotating proxies.")
try:
    scheduler.start()
except (KeyboardInterrupt, SystemExit):
    pass
