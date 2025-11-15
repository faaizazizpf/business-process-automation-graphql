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
