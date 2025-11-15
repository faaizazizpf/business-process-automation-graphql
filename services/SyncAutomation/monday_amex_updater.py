# monday_updater.py
import time
import random
import requests
import json
from datetime import datetime

API_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjUzMjYzNDMzMCwiYWFpIjoxMSwidWlkIjo3NzQyNjMwNSwiaWFkIjoiMjAyNS0wNi0zMFQwOToyNTozMi4xNTZaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6NjExMjgwNywicmduIjoidXNlMSJ9.FQR1op99guHz9QRLGSk1zFH0SaImEWJtBu-2jAIq_x8"
API_URL = "https://api.monday.com/v2"
BOARD_ID = "18206854620"
PERSON_NAME = "faaiz"  # Person to assign

# Column IDs
STATUS_COLUMN_ID = "status"
LAST_MODIFIED_COLUMN_ID = "date4"
PERSON_COLUMN_ID = "person"
SUB_CARD_TYPE = "text_mkwtfhck"
SUB_FILES_DOWNLOADED = "numeric_mkwtjj07"
SUB_STATUS = "status"
SUB_LAST_MODIFIED = "date0"

headers = {
    "Authorization": API_KEY,
    "Content-Type": "application/json"
}


def get_target_item_id(account_name):
    """Fetch all items in the board (beyond 100 limit) and return matching item ID."""
    cursor = None
    while True:
        # Paginated query
        query = f"""
        query ($board_id: [ID!], $cursor: String) {{
          boards(ids: $board_id) {{
            items_page(limit: 100, cursor: $cursor) {{
              cursor
              items {{
                id
                name
              }}
            }}
          }}
        }}
        """

        variables = {"board_id": int(BOARD_ID), "cursor": cursor}
        response = requests.post(API_URL, json={'query': query, 'variables': variables}, headers=headers)

        try:
            data = response.json()["data"]["boards"][0]["items_page"]
        except Exception as e:
            print("❌ Failed to parse Monday API response:", e)
            print(response.text)
            return None

        items = data["items"]
        for item in items:
            if item["name"] == account_name:
                return item["id"]

        # Pagination: if no more pages, stop
        cursor = data.get("cursor")
        if not cursor:
            break

    return None



def get_subitems(parent_item_id):
    query = """
    query ($parent_id: [ID!]) {
      items(ids: $parent_id) {
        subitems {
          id
          name
        }
      }
    }
    """
    variables = {"parent_id": [str(parent_item_id)]}
    response = requests.post(API_URL, headers=headers, json={"query": query, "variables": variables})
    result = response.json()
    if "errors" in result:
        print("❌ Failed to fetch subitems:", result["errors"])
        return []
    return result["data"]["items"][0].get("subitems", [])


def update_main_item(target_item_id,item_status,no_of_cards,parent_folder_url):
    today_str = datetime.now().strftime("%Y-%m-%d")
    column_values = {
        "status": item_status,  # Use label or index directly
        "date4": today_str,  # Date as string
        "numeric_mkx013z8": str(no_of_cards),  # Number as string
        "text_mkwtg2mz":parent_folder_url
    }
    mutation = """
    mutation ($board_id: ID!, $item_id: ID!, $column_values: JSON!) {
      change_multiple_column_values(
        board_id: $board_id,
        item_id: $item_id,
        column_values: $column_values
      ) { id }
    }
    """
    variables = {
        "board_id": BOARD_ID,
        "item_id": target_item_id,
        "column_values": json.dumps(column_values)
    }
    time.sleep(random.uniform(2, 5))
    r = requests.post(API_URL, json={'query': mutation, 'variables': variables}, headers=headers)
    print("🟢 Updated main item:", r.status_code)


def assign_person(target_item_id):
    users_query = "query { users { id name } }"
    time.sleep(random.uniform(2, 5))
    users_resp = requests.post(API_URL, json={'query': users_query}, headers=headers)
    users = users_resp.json()["data"]["users"]

    user_id = next((u["id"] for u in users if u["name"].lower() == PERSON_NAME.lower()), None)
    if not user_id:
        print(f"⚠️ Could not find user '{PERSON_NAME}'")
        return

    mutation = """
    mutation ($board_id: ID!, $item_id: ID!, $column_id: String!, $value: JSON!) {
      change_column_value(board_id: $board_id, item_id: $item_id, column_id: $column_id, value: $value) { id }
    }
    """
    variables = {
        "board_id": BOARD_ID,
        "item_id": target_item_id,
        "column_id": PERSON_COLUMN_ID,
        "value": json.dumps({"personsAndTeams": [{"id": user_id, "kind": "person"}]})
    }
    time.sleep(random.uniform(2, 5))
    r = requests.post(API_URL, json={'query': mutation, 'variables': variables}, headers=headers)
    print("🟢 Assigned person:", r.status_code)

def delete_All_subitems(ITEM_ID):

    # Get subitems of the parent item
    query = """
    query {
      items(ids: [%s]) {
        subitems {
          id
        }
      }
    }
    """ % ITEM_ID

    response = requests.post(
        'https://api.monday.com/v2',
        json={'query': query},
        headers=headers
    )
    data = response.json()
    subitem_ids = [subitem['id'] for subitem in data['data']['items'][0]['subitems']]

    # Delete each subitem
    mutation = """
    mutation ($itemId: Int!) {
      delete_item (item_id: $itemId) {
        id
      }
    }
    """

    for subitem_id in subitem_ids:
        variables = {"itemId": int(subitem_id)}
        requests.post(
            'https://api.monday.com/v2',
            json={'query': mutation, 'variables': variables},
            headers=headers
        )

    print(f"Deleted {len(subitem_ids)} subitems for item {ITEM_ID} on board {BOARD_ID}.")



def delete_subitem(subitem_id):


    # Delete each subitem
    mutation = """
    mutation ($itemId: Int!) {
      delete_item (item_id: $itemId) {
        id
      }
    }
    """

    variables = {"itemId": int(subitem_id)}
    requests.post(
        'https://api.monday.com/v2',
        json={'query': mutation, 'variables': variables},
        headers=headers
    )

    # print(f"Deleted {len(subitem_id)} subitems for item {ITEM_ID} on board {BOARD_ID}.")


# def update_subitem(subitem_id,subitem_data):
#     delete_subitems(subitem_id)


def update_subitem1(subitem_id,subitem_data):
    """Update existing subitem's columns."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    column_values = {
        SUB_CARD_TYPE: {"text": subitem_data["Card Type"]},
        SUB_FILES_DOWNLOADED: {"number": subitem_data["No. of Files Downloaded"]},
        SUB_STATUS: {"label": subitem_data["Status"]},
        SUB_LAST_MODIFIED: {"date": today_str}
    }

    mutation = """
    mutation ($board_id: ID!, $item_id: ID!, $column_values: JSON!) {
      change_multiple_column_values(board_id: $board_id, item_id: $item_id, column_values: $column_values) {
        id
      }
    }
    """
    variables = {
        "board_id": BOARD_ID,
        "item_id": subitem_id,
        "column_values": json.dumps(column_values)
    }
    time.sleep(random.uniform(2, 5))
    r = requests.post(API_URL, json={'query': mutation, 'variables': variables}, headers=headers)

    print(f"🟡 Updated existing subitem {subitem_id}: {r.status_code}")
    print("Full API RESPONSE:", r.json())
today_str = datetime.now().strftime("%Y-%m-%d")


def delete_item(item_id):
    mutation = """
    mutation ($item_id: ID!) {
    delete_item (item_id: $item_id) {
        id
    }
    }
    """
    variables = {"item_id": str(item_id)}

    response = requests.post(
        API_URL,
        headers=headers,
        json={"query": mutation, "variables": variables}
    )

    result = response.json()
    if "errors" in result:
        print(f"❌ Failed to delete subitem {item_id}: {result['errors']}")
        return False
    print(f"🗑️ Deleted subitem {item_id}")
    return True


def create_subitem(parent_item_id, subitem_name, subitem_data):
    mutation = """
    mutation ($parent_id: ID!, $item_name: String!, $column_values: JSON!) {
    create_subitem(parent_item_id: $parent_id, item_name: $item_name, column_values: $column_values) {
        id
        name
    }
    }
    """
    # Name                           → id: name, type: name
    # Card Type                      → id: text_mkwtfhck, type: text
    # No. of Files Downloaded        → id: numeric_mkwtjj07, type: numbers
    # Status                         → id: status, type: status
    # Remarks/Notes                  → id: text_mkwtasrd, type: text
    # Last Modified                  → id: date0, type: date
    # GDrive Folder Link             → id: text_mkx0f9q8, type: text

    # subitems_data = [
    #     {"Card Type": "Business", "No. of Files Downloaded": "22", "Card Account": "9-00112", "Status": "Completed",
    #      "folder_url": "https://drive.google.com/drive/folders/1ssGFQBSgcGH15H0HS8Lh4bK-rLFmaxq7"},
    #     {"Card Type": "Golden", "No. of Files Downloaded": "11", "Card Account": "2-00774", "Status": "In Progress",
    #      "folder_url": "https://drive.google.com/drive/folders/1ssGFQBSgcGH15H0HS8Lh4bK-rLFmaxq7"}
    # ]
    variables = {
        "parent_id": str(parent_item_id),
        "item_name": subitem_name,
        "column_values": json.dumps({
            "status": subitem_data["Status"],
            "name": subitem_data["Card Account"],
            "numeric_mkwtjj07": subitem_data["No. of Files Downloaded"],
            "text_mkwtfhck": subitem_data["Card Type"],
            "date0": today_str,
            "text_mkx0f9q8": subitem_data["folder_url"]

        })
    }
    random_float = random.uniform(2, 5)
    time.sleep(random_float)
    response = requests.post(
        API_URL,
        headers=headers,
        json={"query": mutation, "variables": variables}
    )

    try:
        result = response.json()
    except Exception as e:
        print("❌ JSON decode failed:", str(e))
        print(response.text)
        return None

    if "errors" in result:
        print(f"❌ GraphQL Error creating subitem '{subitem_name}':")
        for err in result["errors"]:
            print("-", err["message"])
        return None

    if "data" in result and result["data"]["create_subitem"]:
        sub_id = result["data"]["create_subitem"]["id"]
        print(f"✅ Subitem '{subitem_name}' created under item {parent_item_id}")
        return sub_id
    else:
        print(f"⚠️ Unexpected response while creating subitem '{subitem_name}':")
        print(json.dumps(result, indent=2))
        return None


# sub_mutation = """
# mutation ($board_id: ID!, $item_id: ID!, $column_values: JSON!) {
#   change_multiple_column_values(board_id: $board_id, item_id: $item_id, column_values: $column_values) {
#     id
#   }
# }
# """
# vars_update = {
#     "board_id": SUBITEM_BOARD_ID,
#     "item_id": subitem_id,
#     "column_values": json.dumps(column_values)
# }
# upd_resp = requests.post(API_URL, json={'query': sub_mutation, 'variables': vars_update}, headers=headers)

def create_main_item(account_name):
    """Create a new main item if account doesn't exist."""
    mutation = """
    mutation ($board_id: ID!, $item_name: String!) {
      create_item(board_id: $board_id, item_name: $item_name) {
        id
        name
      }
    }
    """
    variables = {
        "board_id": BOARD_ID,
        "item_name": account_name
    }

    time.sleep(random.uniform(2, 5))
    response = requests.post(API_URL, headers=headers, json={"query": mutation, "variables": variables})

    try:
        result = response.json()
    except Exception as e:
        print("❌ Failed to decode create_main_item response:", str(e))
        print(response.text)
        return None

    if "errors" in result:
        print(f"❌ Error creating main item '{account_name}':", result["errors"])
        return None

    item_id = result["data"]["create_item"]["id"]
    print(f"✅ Created new main item '{account_name}' (ID: {item_id})")
    return item_id

# update_monday_board(account_name, subitems_data,no_of_cards, item_status,parent_folder_url, True)

def update_monday_board(account_name, subitems_data, no_of_cards, item_status, parent_folder_url, clean_subItems):
    """Main function to update Monday board and sync subitems."""
    target_item_id = get_target_item_id(account_name)

    if not target_item_id:
        print(f"⚠️ No item found for account '{account_name}', creating new one...")
        target_item_id = create_main_item(account_name)
        if not target_item_id:
            print("❌ Failed to create new main item, aborting.")
            return

    print(f"✅ Found main item ID: {target_item_id}")
    update_main_item(target_item_id, item_status,no_of_cards,parent_folder_url)
    assign_person(target_item_id)

    existing_subitems = get_subitems(target_item_id)
    existing_map = {sub["name"]: sub["id"] for sub in existing_subitems}
    # delete_All_subitems(target_item_id)
    # ONLY CLEAN SUBITEMS IF ITS FIRST CARD IGNORE CLEANING AND GOT STRAIGTH TO ADDING
    if clean_subItems:
        for sub in existing_subitems:
            delete_item(sub["id"])

    for sub in subitems_data:
        card_account = sub["Card Account"]
    #     # if card_account in existing_map:
    #     #     delete_subitem(existing_map[card_account])
    #     #     update_subitem(existing_map[card_account],sub)
    #     # else:
        create_subitem(target_item_id,card_account, sub)

    print("\n✅ Done — main item and subitems synced successfully.")

    print("\n✅ Done — main item and subitems synced successfully.")


