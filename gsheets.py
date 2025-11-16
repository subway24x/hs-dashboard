import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st


def get_gspread_client():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    # Load credentials from Streamlit Cloud secrets
    creds = Credentials.from_service_account_info(st.secrets, scopes=scope)

    return gspread.authorize(creds)


def load_sheet(sheet_name: str, worksheet_name: str) -> pd.DataFrame:
    client = get_gspread_client()

    sheet = client.open(sheet_name).worksheet(worksheet_name)
    raw = sheet.get_all_values()

    headers = raw[0]

    # Fix blank or duplicate headers
    fixed_headers = []
    used = set()
    blank_count = 1

    for h in headers:
        h_clean = h.strip()

        if h_clean == "":
            h_clean = f"blank_{blank_count}"
            blank_count += 1

        if h_clean in used:
            h_clean = h_clean + "_dup"

        used.add(h_clean)
        fixed_headers.append(h_clean)

    df = pd.DataFrame(raw[1:], columns=fixed_headers)
    return df
