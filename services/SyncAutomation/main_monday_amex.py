from monday_amex_updater import update_monday_board

account_name = "bitrogroupinc"
no_of_cards=22
subitems_data = [
    {"Card Type": "Business", "No. of Files Downloaded": "22", "Card Account": "9-00112", "Status": "Completed","folder_url":"https://drive.google.com/drive/folders/1ssGFQBSgcGH15H0HS8Lh4bK-rLFmaxq7"},
    {"Card Type": "Golden", "No. of Files Downloaded": "11", "Card Account": "2-00774", "Status": "In Progress","folder_url":"https://drive.google.com/drive/folders/1ssGFQBSgcGH15H0HS8Lh4bK-rLFmaxq7"}
]


item_status="Completed"
parent_folder_url="https://drive.google.com/drive/folders/1nG126uzn7Lz0WR46Tv2JlFLz2Mj5iygw"
update_monday_board(account_name, subitems_data,no_of_cards, item_status,parent_folder_url, True)
