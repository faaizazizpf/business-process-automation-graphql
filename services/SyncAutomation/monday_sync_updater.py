import requests
import json
import requests
import json
from utils import *
API_KEY = 'eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjUzMjYzNDMzMCwiYWFpIjoxMSwidWlkIjo3NzQyNjMwNSwiaWFkIjoiMjAyNS0wNi0zMFQwOToyNTozMi4xNTZaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6NjExMjgwNywicmduIjoidXNlMSJ9.FQR1op99guHz9QRLGSk1zFH0SaImEWJtBu-2jAIq_x8'
BOARD_ID = 9415114344


class MondaySubitemColumnHelper:

    def init(self, api_key):
        self.api_key = api_key
        self.api_url = "https://api.monday.com/v2"
        self.headers = {
        "Authorization": self.api_key,
        "Content-Type": "application/json"
        }
    
    def get_subitem_board_id(self):
        """Fetch the board ID of the default Subitems board"""
        query = """
        query {
        boards (limit: 50) {
            id
            name
            board_kind
        }
        }
        """
        response = requests.post(self.api_url, headers=self.headers, json={"query": query})
        data = response.json()
        for board in data["data"]["boards"]:
            if board["board_kind"] == "subtasks_board":
                return board["id"]
        return None

    def get_subitem_status_labels(self):
        """Fetch and print the available labels in the subitem board's Status column"""
        subitem_board_id = self.get_subitem_board_id()
        if not subitem_board_id:
            print("❌ Subitem board not found.")
            return

        query = """
        query ($board_id: [Int]) {
        boards(ids: $board_id) {
            columns {
            id
            title
            type
            settings_str
            }
        }
        }
        """
        variables = {"board_id": int(subitem_board_id)}
        response = requests.post(self.api_url, headers=self.headers, json={"query": query, "variables": variables})
        result = response.json()

        if "errors" in result:
            print("❌ Error fetching subitem columns:", result["errors"])
            return

        columns = result["data"]["boards"][0]["columns"]
        for col in columns:
            if col["type"] == "status":
                print(f"🟦 Status Column: {col['title']} (id: {col['id']})")
                settings = json.loads(col["settings_str"])
                labels = settings.get("labels", {})
                for k, v in labels.items():
                    print(f"  {k}: {v}")
                return

        print("⚠️ No status column found in subitem board.")



class MondaySyncUpdater:
    def __init__(self, api_key, board_id):
        self.api_key = api_key
        self.board_id = str(board_id)
        self.api_url = 'https://api.monday.com/v2'
        self.headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json"
        }

    def _query_items(self):
        query = f"""
        query {{
          boards(ids: [{self.board_id}]) {{
            items_page(limit: 100) {{
              items {{
                id
                name
                column_values {{
                  id
                  text
                }}
              }}
            }}
          }}
        }}
        """
        response = requests.post(self.api_url, json={'query': query}, headers=self.headers)
        if response.status_code == 200:
            return response.json()['data']['boards'][0]['items_page']['items']
        else:
            raise Exception(f"Failed to query board items: {response.status_code} {response.text}")

    def _find_item_id_by_email(self, items, email_to_match):
        for item in items:
            for col in item['column_values']:
                if col['id'] == "text_mks2a1av" and col['text'] == email_to_match:
                    return item['id']
        return None



    def get_subitems(self, parent_item_id):
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

        response = requests.post(
            self.api_url,
            headers=self.headers,
            json={"query": query, "variables": variables}
        )

        result = response.json()
        if "errors" in result:
            print("❌ Failed to fetch subitems:", result["errors"])
            return []

        return result["data"]["items"][0].get("subitems", [])


    def delete_item(self, item_id):
        mutation = """
        mutation ($item_id: ID!) {
        delete_item (item_id: $item_id) {
            id
        }
        }
        """
        variables = {"item_id": str(item_id)}

        response = requests.post(
            self.api_url,
            headers=self.headers,
            json={"query": mutation, "variables": variables}
        )

        result = response.json()
        if "errors" in result:
            print(f"❌ Failed to delete subitem {item_id}: {result['errors']}")
            return False
        print(f"🗑️ Deleted subitem {item_id}")
        return True


    def create_subitem(self, parent_item_id, subitem_name, status_label="Out of Sync"):
        mutation = """
        mutation ($parent_id: ID!, $item_name: String!, $column_values: JSON!) {
        create_subitem(parent_item_id: $parent_id, item_name: $item_name, column_values: $column_values) {
            id
            name
        }
        }
        """

        variables = {
            "parent_id": str(parent_item_id),  # MUST be string
            "item_name": subitem_name,
            "column_values": json.dumps({
                "status": {"label": status_label}
            })
        }

        response = requests.post(
            self.api_url,
            headers=self.headers,
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


    def update_status(self, email, status_label, out_of_sync_accounts=None):


        

        # stopper("update_status(self, email, status_label, out_of_sync_accounts=None)")


        valid_labels = ["Out of Sync", "Login Issue", "Sync", ""]  # "" means clear

        if status_label not in valid_labels:
            raise ValueError(f"Invalid status: '{status_label}'. Must be one of {valid_labels}")

        items = self._query_items()
        item_id = self._find_item_id_by_email(items, email)

        if not item_id:
            print(f"No item found for email: {email}")
            return False

        # GraphQL mutation
        mutation = """
        mutation ($board_id: ID!, $item_id: ID!, $column_id: String!, $value: JSON!) {
        change_column_value(board_id: $board_id, item_id: $item_id, column_id: $column_id, value: $value) {
            id
        }
        }
        """

        # Prepare value for mutation
        if status_label == "":
            # Clear the status using index -1
            value_json = json.dumps({"index": 3})
        else:
            value_json = json.dumps({"label": status_label})

        variables = {
            "board_id": self.board_id,
            "item_id": item_id,
            "column_id": "status",
            "value": value_json
        }

        response = requests.post(self.api_url, json={'query': mutation, 'variables': variables}, headers=self.headers)

        

        if response.status_code == 200:
            print(f"✅ Updated status for '{email}' to '{status_label or 'CLEARED'}'")
            
            if status_label == "Out of Sync" and out_of_sync_accounts:
            


                # if out_of_sync_accounts != None:   
                #     out_of_sync_accounts1=[]
                #     for element in out_of_sync_accounts:
                #         if element != '' and element != None:
                #             out_of_sync_accounts1.append(element)

                #     out_of_sync_accounts=out_of_sync_accounts1


                existing_subitems = self.get_subitems(item_id)
                for sub in existing_subitems:
                    self.delete_item(sub["id"])
                print(f"🔁 Creating subitems for out-of-sync banks: {[el for el in out_of_sync_accounts]}")
                # Remove old subitems first
                existing_subitems = self.get_subitems(item_id)
                for sub in existing_subitems:
                    self.delete_item(sub["id"])

                # Create new subitems
                for bank_name in out_of_sync_accounts:
                    self.create_subitem(parent_item_id=item_id, subitem_name=bank_name)
            return True
        else:
            print(f"❌ Failed to update status for '{email}':", response.status_code, response.text)
            return False
