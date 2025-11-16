import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

SPREADSHEET_NAME = "HS SPREADSHEET NEW ROSTER"
WORKSHEET_NAME = "All Match History"

def load_clean_data():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open(SPREADSHEET_NAME).worksheet(WORKSHEET_NAME)

    raw = sheet.get_all_values()

    HEADER_ROW = 2
    headers = raw[HEADER_ROW]
    rows = raw[HEADER_ROW + 1:]

    df = pd.DataFrame(rows, columns=headers)

    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    df = df[df["Opponent"].notna() & (df["Opponent"] != "")]

    # Combine 3 roster columns → 1
    roster_cols = [c for c in df.columns if "Roster" in c or "Pink" in c or "Cyan" in c]
    if roster_cols:
        df["Rosters"] = df[roster_cols].apply(lambda r: 
            " | ".join([v for v in r if v.strip()]), axis=1)
        df = df.drop(columns=roster_cols)

    final_columns = [
        "Opponent", "DATE", "TIME (SGT)", "Played", "Differential",
        "Won", "Lost", "ATK W", "ATK L", "DEF W", "DEF L",
        "Type of Match", "Map", "Result", "Game Level",
        "Scrim Quality", "VOD Link", "Notes",
        "Rosters", "Pistols (ATK)", "Pistols (DEF)", "Comp"
    ]

    df = df.reindex(columns=[c for c in final_columns if c in df.columns])

    return df.reset_index(drop=True)
