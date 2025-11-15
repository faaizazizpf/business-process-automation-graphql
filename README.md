
# 🧠 Zoe Data Sync

A scheduled data synchronization tool that pulls user **Buxfer** account and transaction data using rotating proxies, configurable via **Google Sheets**, and stores the data in a **PostgreSQL** database.

> 🔗 Repo: [https://github.com/zoesols/zoe_data_sync](https://github.com/zoesols/zoe_data_sync)

----------

## 🚀 Features

-   ⏰ **Scheduled per-user jobs** via Google Sheets (`HH:MM`)
    
-   🔁 **Rotating proxy** support from spreadsheet-configured IPs
    
-   🔐 Authenticates and fetches from the **Buxfer API**
    
-   🗃️ Saves transactions & accounts to a **PostgreSQL** database
    
-   🧾 Tracks progress per user and updates **Google Sheet**
    

----------

## 🛠 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/zoesols/zoe_data_sync.git
cd zoe_data_sync

```

----------

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

```

----------

### 3. Install Dependencies

```bash
pip install -r requirements.txt

```

----------

### 4. Configure `.env` File

Create a `.env` file in the root with the following content:

```env
SECRET_KEY=kahitano
API_BASE_URL=https://www.buxfer.com/api
SPREADSHEET_ID=1KzhniGhT-tAxvnGg3JavdP7KLNo2w_qAw2jNu1W1qvc

DB_NAME=postgres
DB_USER=postgres
DB_PORT=5432
DB_HOST=localhost
DB_PASSWORD=root

```

----------

### 5. Add Google API Credentials

-   Go to [Google Cloud Console](https://console.cloud.google.com/)
    
-   Create a **Service Account**
    
-   Enable the **Google Sheets API**
    
-   Share the spreadsheet with the service account email
    
-   Download the key and save it as `credentials.json` in the root of the project
    

----------

## 📄 Google Spreadsheet Format

### 🧾 Sheet: `BUXFER ACCOUNTS`

A

B (Username)

C (Password)

...

G (Time `HH:MM`)

H (Last Page Synced)

1

[user@example.com](mailto:user@example.com)

mypassword

...

09:00

1

----------

### 🧾 Sheet: `Mobile Proxy`

A

B (Public IP)

...

E (External Port)

1

123.45.67.89

...

8000

----------

## 🧰 Database Setup

Make sure you have PostgreSQL running and create the database:

```bash
createdb -U postgres postgres

```

Your SQLAlchemy models should match the expected schema from Buxfer (found in `models/`).

----------

## 🏃 Run the Scheduler

```bash
python main.py

```

✅ What it does:

-   Loads user schedule from Google Sheet
    
-   Authenticates with Buxfer using proxies
    
-   Fetches accounts and transactions
    
-   Saves to PostgreSQL
    
-   Updates synced page number in sheet
    

----------

## 🗂 Project Structure

```
zoe_data_sync/
├── main.py
├── services/
│   └── buxfer_service.py
├── models/
│   ├── buxfer_accounts.py
│   └── buxfer_transactions.py
├── .env
├── credentials.json
├── requirements.txt
└── README.md

```

----------

## 📦 Sample `requirements.txt`

```
python-dotenv
apscheduler
google-api-python-client
google-auth
requests
SQLAlchemy
psycopg2-binary

```

----------

## 📌 Notes

-   Make sure schedule times are in 24-hour `HH:MM` format
    
-   The script runs indefinitely and should be deployed on a background process/server
    
-   Rotate proxies as needed via the Google Sheet
    
