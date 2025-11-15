import os
import csv
import json
import time
import requests
from dotenv import load_dotenv
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from models.buxfer_transactions import BuxferTransaction

from services.db import SessionLocal
from models.buxfer_transactions import BuxferTransaction
from models.buxfer_accounts import BuxferAccount

load_dotenv()

user_token_map = {}

SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/spreadsheets'
]
SERVICE_ACCOUNT_FILE = 'credentials.json'
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

def get_proxies():
    try:
        service = build('sheets', 'v4', credentials=credentials)
        spreadsheet_id = os.getenv('SPREADSHEET_ID')
        range_name = 'Mobile Proxy!A:F'

        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
        values = result.get('values', [])[1:]

        proxies = []
        for row in values:
            if len(row) >= 5:
                public_ip, external_port = row[1], row[4]
                proxies.append({
                    'http': f'http://{public_ip}:{external_port}',
                    'https': f'http://{public_ip}:{external_port}'
                })

        return proxies
    except Exception as e:
        print("Error fetching proxies:", e)
        return []

def get_valid_token(session, user_name, password):
    if user_name in user_token_map:
        return user_token_map[user_name]
    token = login(session, user_name, password)
    user_token_map[user_name] = token
    return token

def login(session, email, password):
    url = f"{os.getenv('API_BASE_URL')}/login"
    params = {'email': email, 'password': password}
    response = session.post(url, params=params)
    response.raise_for_status()
    data = response.json()
    if 'response' in data and 'token' in data['response']:
        return data['response']['token']
    raise ValueError("No token received")

def fetch_transactions(session, token, page, user_name):
    url = f"{os.getenv('API_BASE_URL')}/transactions"
    headers = {'Authorization': f"Bearer {os.getenv('API_KEY')}"}
    params = {'token': token, 'page': page}
    response = session.get(url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()

    transactions = data.get('response', {}).get('transactions', [])
    if not transactions:
        return False

    db = SessionLocal()
    try:
        for tx in transactions:
            tx['userName'] = user_name
            if 'id' in tx:
                db_tx = BuxferTransaction(**tx)
                db.merge(db_tx)  # Upsert using primary key `id`
        db.commit()
        print(f"Upserted {len(transactions)} transactions for {user_name} (page {page})")
        return True
    except Exception as e:
        db.rollback()
        print("Error saving transactions:", e)
        return False
    finally:
        db.close()

def fetch_accounts(session, token, user_name):
    url = f"{os.getenv('API_BASE_URL')}/accounts"
    headers = {'Authorization': f"Bearer {os.getenv('API_KEY')}"}
    params = {'token': token}
    response = session.get(url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()

    accounts = data.get('response', {}).get('accounts', [])
    if not accounts:
        return

    db = SessionLocal()
    try:
        for acc in accounts:
            acc['userName'] = user_name
            if 'id' in acc:
                db_acc = BuxferAccount(**acc)
                db.merge(db_acc)  # Upsert using primary key `id`
        db.commit()
        print(f"Upserted {len(accounts)} accounts for {user_name}")
    except Exception as e:
        db.rollback()
        print("Error saving accounts:", e)
    finally:
        db.close()

def update_page_in_spreadsheet(user_name, new_page):
    try:
        service = build('sheets', 'v4', credentials=credentials)
        spreadsheet_id = os.getenv('SPREADSHEET_ID')
        range_name = 'BUXFER ACCOUNTS!A:H'

        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
        values = result.get('values', [])[1:]
        header = result.get('values', [])[0] if result.get('values') else []

        updated_values = []
        for row in values:
            if row[1] == user_name:
                while len(row) <= 7:
                    row.append('')
                row[7] = str(new_page)
            updated_values.append(row)

            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption="RAW",
                body={"values": [header] + updated_values}
            ).execute()

        print(f"Updated page number for {user_name}: {new_page}")

    except Exception as e:
        print("Error updating page number:", e)

def log_failed_proxy(proxy, user_name, reason=""):
    try:
        service = build('sheets', 'v4', credentials=credentials)
        spreadsheet_id = os.getenv('SPREADSHEET_ID')
        range_name = 'FAILED PROXY!A:D'

        # Log format: timestamp, user, proxy_ip:port, reason
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        proxy_str = proxy.get('http', 'N/A')
        values = [[timestamp, user_name, proxy_str, reason]]

        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": values}
        ).execute()
    except Exception as e:
        print("Error logging failed proxy:", e)


def save_buxfer_data(user_name):
    try:
        service = build('sheets', 'v4', credentials=credentials)
        spreadsheet_id = os.getenv('SPREADSHEET_ID')
        range_name = 'BUXFER ACCOUNTS!A:H'

        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
        values = result.get('values', [])[1:]

        proxy_list = get_proxies()
        if not proxy_list:
            print("No proxies available! Exiting.")
            return

        for idx, user in enumerate(values):
            if user[1] != user_name:
                continue

            password = user[2]
            try:
                current_page = int(user[7])
            except (IndexError, ValueError):
                current_page = 1

            token = None
            for proxy in proxy_list:
                session = requests.Session()
                session.proxies.update(proxy)
                session.trust_env = False

                try:
                    print(f"\n[START] Using proxy {proxy['https']} for {user_name} starting at page {current_page}")

                    # Only login if no token exists or previously failed
                    if not token:
                        try:
                            token = get_valid_token(session, user_name, password)
                        except Exception as login_err:
                            print(f"Login failed for {user_name}: {login_err}")
                            break

                    # Fetch accounts (retry login if fails)
                    try:
                        fetch_accounts(session, token, user_name)
                    except Exception as acc_err:
                        print(f"Account fetch failed, retrying login: {acc_err}")
                        token = login(session, user_name, password)
                        fetch_accounts(session, token, user_name)

                    time.sleep(5)

                    # Fetch 5 pages of transactions
                    pages_fetched = 0
                    for i in range(current_page, current_page + 5):
                        try:
                            has_more_data = fetch_transactions(session, token, i, user_name)
                            if not has_more_data:
                                print(f"No more transactions for {user_name} at page {i}")
                                break
                            pages_fetched += 1
                            time.sleep(2)
                        except Exception as tx_err:
                            print(f"Transaction fetch failed at page {i}, retrying login: {tx_err}")
                            token = login(session, user_name, password)
                            break  # Break loop and retry with next proxy

                    if pages_fetched > 0:
                        update_page_in_spreadsheet(user_name, current_page + pages_fetched)
                    break  # success, break proxy loop

                except Exception as e:
                    print(f"Error with proxy {proxy['http']} for {user_name}:", e)
                    log_failed_proxy(proxy, user_name, str(e))
                    time.sleep(5)

            time.sleep(20)  # Wait 20 seconds between users

    except Exception as e:
        print('Error in save_buxfer_data:', e)

def export_all_transactions_to_drive():
    try:
        # Step 1: Fetch all transactions from DB
        db = SessionLocal()
        transactions = db.query(BuxferTransaction).all()
        db.close()

        if not transactions:
            print("No transactions found.")
            return

        # Step 2: Write to CSV
        date_str = datetime.now().strftime('%Y-%m-%d')
        csv_file = f"buxfer_transactions_export_{date_str}.csv"
        with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)

            # Write header
            sample_tx = transactions[0].__dict__.copy()
            sample_tx.pop("_sa_instance_state", None)
            headers = list(sample_tx.keys())
            writer.writerow(headers)

            # Write each transaction
            for tx in transactions:
                row = [getattr(tx, field) for field in headers]
                writer.writerow(row)

        print(f"CSV written with {len(transactions)} transactions.")

        # Step 3: Upload to Google Drive
        service = build('drive', 'v3', credentials=credentials)
        file_metadata = {
            'name': csv_file,
            'parents': ['1k-GNe-clxxQjD598jVoc6b6WXuaALbPF']
        }
        media = MediaFileUpload(csv_file, mimetype='text/csv')
        uploaded_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        print(f"CSV uploaded successfully to Drive. File ID: {uploaded_file.get('id')}")

    except Exception as e:
        print("Error exporting and uploading transactions:", e)
