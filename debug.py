import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name(
    "service_account.json", scope
)

client = gspread.authorize(creds)

print("Listing all spreadsheets the service account can see:\n")
files = client.list_spreadsheet_files()

for f in files:
    print(f["name"])
