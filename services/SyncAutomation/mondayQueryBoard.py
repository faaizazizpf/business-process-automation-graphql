import requests
# Replace with your actual API key and board ID
import json
from pprint import pprint


api_key = ""
board_id = ""  # Replace with your actual board ID

url = "https://api.monday.com/v2"

query = """
query {
  boards(ids: %s) {
    name
    items_page(limit: 100) {
      items {
        id
        name
        column_values {
          id
          text
          value
          type
        }
      }
    }
  }
}
""" % board_id

headers = {
    "Authorization": api_key,
    "Content-Type": "application/json"
}

response = requests.post(url, json={"query": query}, headers=headers)

if response.status_code == 200:
    data = response.json()
    with open("demofile.txt", "a") as f:
      f.write(str(data))

    # #open and read the file after the appending:
    # with open("demofile.txt") as f:
    #   print(f.read())
    pprint(data)
else:
    print("Query failed:", response.text)
