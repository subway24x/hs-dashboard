import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials


# -----------------------------------------------------------
# PAGE CONFIG
# -----------------------------------------------------------
st.set_page_config(
    page_title="Match History — Heaven Sent",
    layout="wide"
)

SPREADSHEET_NAME = "HS SPREADSHEET NEW ROSTER"
WORKSHEET_NAME = "All Match History"

# -----------------------------------------------------------
# LOAD DATA FROM GOOGLE SHEETS
# -----------------------------------------------------------
@st.cache_data
def load_match_history():
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            "service_account.json", scope
        )
        client = gspread.authorize(creds)

        sheet = client.open(SPREADSHEET_NAME).worksheet(WORKSHEET_NAME)
        raw = sheet.get_all_values()

        HEADER_ROW = 2  # Your sheet's header row
        headers = raw[HEADER_ROW]
        rows = raw[HEADER_ROW + 1:]

        df = pd.DataFrame(rows, columns=headers)

        # Remove useless/duplicate columns
        df = df.loc[:, df.columns.notna()]
        df = df.loc[:, df.columns != ""]
        df = df.loc[:, ~df.columns.duplicated()]

        # Drop empty Opponent rows
        if "Opponent" in df.columns:
            df = df[df["Opponent"].notna() & (df["Opponent"] != "")]

        return df

    except Exception as e:
        st.error(f"❌ Error loading Match History sheet: {e}")
        return None

# -----------------------------------------------------------
# CLEAN + FORMAT DATAFRAME
# -----------------------------------------------------------
def clean_history(df):
    df = df.copy()

    # Trim whitespace
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

    # Roster column auto-detection
    roster_cols = [
        col
        for col in df.columns
        if "oster" in col.lower() or "pink" in col.lower() or "cyan" in col.lower()
    ]

    if roster_cols:
        df["Rosters"] = df[roster_cols].apply(
            lambda x: " | ".join([v for v in x if v.strip() != ""]),
            axis=1
        )
        df = df.drop(columns=roster_cols)

    # Automated renaming corrections
    rename_map = {
        "TIME(SGT)": "TIME (SGT)",
        "Pistols (ATK)": "Pistols (ATK)",
        "Pistols (DEF)": "Pistols (DEF)",
        "Game Level": "Game Level",
        "Scrim Quality": "Scrim Quality",
        "VOD Link": "VOD Link",
    }
    df = df.rename(columns=rename_map)

    # Ordered table
    desired_order = [
        "Opponent", "DATE", "TIME (SGT)", "Played", "Differential",
        "Won", "Lost",
        "ATK W", "ATK L", "DEF W", "DEF L",
        "Type of Match", "Map", "Result",
        "Game Level", "Scrim Quality",
        "VOD Link", "Notes", "Rosters",
        "Pistols (ATK)", "Pistols (DEF)",
        "Comp"
    ]

    df = df.reindex(columns=[c for c in desired_order if c in df.columns])

    return df.reset_index(drop=True)

# -----------------------------------------------------------
# PAGE UI
# -----------------------------------------------------------
st.image("heaven_sent_logo.png", width=100)
st.markdown(
    "<h1 style='color:#D4AF37;'>Match History — Full Logs</h1>",
    unsafe_allow_html=True
)

raw_df = load_match_history()
if raw_df is None:
    st.stop()

try:
    df = clean_history(raw_df)
    st.success("Match History Loaded Successfully!")
except Exception as e:
    st.error(f"❌ Error processing match history: {e}")
    st.stop()

# -----------------------------------------------------------
# DISPLAY TABLE
# -----------------------------------------------------------
st.subheader("📘 Cleaned Match History")
st.dataframe(df, use_container_width=True)
