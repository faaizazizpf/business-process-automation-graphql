from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup Google Sheets credentials
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SERVICE_ACCOUNT_FILE = 'credentials.json'

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
def get_all_buxfer_users():
    accounts=[]
    try:
        service = build('sheets', 'v4', credentials=credentials)
        spreadsheet_id = os.getenv('SPREADSHEET_ID')
        range_name = 'BUXFER ACCOUNTS!A:H'

        sheet = service.spreadsheets()
        result = sheet.values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()
        values = result.get('values', [])[1:]  # Skip header

        print("All Buxfer Accounts (Email, Password):\n")
        
        for row in values:
            dic={}
            email = row[1] if len(row) > 1 else 'N/A'
            password = row[2] if len(row) > 2 else 'N/A'
            dic["Email"]=email
            dic["Password"]=password
            accounts.append(dic)
            # print(f"Email: {email} | Password: {password}")
        return accounts
    except Exception as e:
        print("Error fetching Buxfer account data:", e)

# Call this function to print
# print(get_all_buxfer_users())
