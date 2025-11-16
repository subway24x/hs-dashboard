import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

def load_sheet(sheet_name: str, worksheet_name: str) -> pd.DataFrame:
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "service_account.json",
        scope
    )

    client = gspread.authorize(creds)
    sheet = client.open(sheet_name).worksheet(worksheet_name)

    # Read raw sheet values (does NOT enforce header rules)
    raw = sheet.get_all_values()

    # First row is header — but may contain duplicates/blanks
    headers = raw[0]

    # Fix blank or duplicate headers
    fixed_headers = []
    used = set()
    blank_count = 1

    for h in headers:
        h_clean = h.strip()

        # Replace blank header names
        if h_clean == "":
            h_clean = f"blank_{blank_count}"
            blank_count += 1

        # Prevent duplicate headers
        if h_clean in used:
            h_clean = h_clean + "_dup"

        used.add(h_clean)
        fixed_headers.append(h_clean)

    # Build DataFrame using the cleaned headers
    df = pd.DataFrame(raw[1:], columns=fixed_headers)
    return df
