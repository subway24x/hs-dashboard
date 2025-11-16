import streamlit as st
import pandas as pd
import numpy as np
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import altair as alt


st.set_page_config(page_title="Player Agent Stats", layout="wide")
LOGO = "heaven_sent_logo.png"

col1, col2 = st.columns([1, 8])
with col1:
    st.image(LOGO, width=75)
with col2:
    st.markdown("<h1 style='color:#d4af37;'>Player Agent Stats</h1>", unsafe_allow_html=True)


# ---------------------------------------------------------
# GOOGLE SHEETS LOADER
# ---------------------------------------------------------
@st.cache_data
def load_sheet():
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
    client = gspread.authorize(creds)

    sheet = client.open("HS SPREADSHEET NEW ROSTER").worksheet("Scrim Stats")
    return sheet.get_all_values()

raw = load_sheet()
df = pd.DataFrame(raw)


# ---------------------------------------------------------
# FIXED PLAYER COLUMN MAPPING
# ---------------------------------------------------------
PLAYER_BLOCKS = {
    "Rus":      (14, 21),
    "Solo":     (22, 29),
    "Jayloh":   (30, 37),
    "Slash":    (38, 45),
    "Jfz":      (46, 53),
    "Synzera":  (54, 61),
}

players = list(PLAYER_BLOCKS.keys())
selected = st.selectbox("Select Player", players)

HEADER_ROW = 5
DATA_START_ROW = 6


# ---------------------------------------------------------
# BLOCK EXTRACTOR
# ---------------------------------------------------------
def extract_player_block(player):
    start_col, end_col = PLAYER_BLOCKS[player]
    end_col += 1

    headers = df.iloc[HEADER_ROW, start_col:end_col].tolist()
    headers = [h if h != "" else f"Col{i}" for i, h in enumerate(headers)]

    EXPECTED_HEADERS = ["KDA","Kills","Deaths","Assists","ACS","FK","FD","Agent"]
    if len(headers) == 8:
        headers = EXPECTED_HEADERS

    data = []
    r = DATA_START_ROW

    while r < len(df):
        row = df.iloc[r, start_col:end_col].tolist()

        if all(str(x).strip() == "" for x in row):
            break

        if all(str(x).strip() in ["", "N/A"] for x in row):
            r += 1
            continue

        data.append(row)
        r += 1

    if not data:
        return None

    player_df = pd.DataFrame(data, columns=headers)
    player_df["Player"] = player  # ⭐ IMPORTANT: add player name column
    player_df.replace(["", "N/A"], np.nan, inplace=True)

    return player_df


# ---------------------------------------------------------
# BUILD FULL PLAYER DATAFRAME (for benchmark page)
# ---------------------------------------------------------
full_blocks = []

for p in players:
    temp = extract_player_block(p)
    if temp is not None:
        full_blocks.append(temp)

if len(full_blocks) == 0:
    st.error("❌ No player data found!")
    st.stop()

full_df = pd.concat(full_blocks, ignore_index=True)

# ⭐ SAVE INTO SESSION STATE FOR BENCHMARK PAGE
st.session_state["player_stats_df"] = full_df



# ---------------------------------------------------------
# UI FOR SELECTED PLAYER
# ---------------------------------------------------------
player_df = full_df[full_df["Player"] == selected]

st.subheader(f"{selected} Scrim Stats")
st.dataframe(player_df, use_container_width=True)


# ---------------------------------------------------------
# AGENT USAGE CHART
# ---------------------------------------------------------
agent_col = None
for col in player_df.columns:
    if col.lower().strip() in ["agent", "agent played"]:
        agent_col = col
        break

if agent_col:
    st.subheader(f"{selected} – Agent Usage")

    agent_counts = (
        player_df[agent_col]
        .dropna()
        .value_counts()
        .reset_index()
    )
    agent_counts.columns = ["Agent", "Count"]

    chart = (
        alt.Chart(agent_counts)
        .mark_bar(size=25)
        .encode(
            x=alt.X("Agent:N", axis=alt.Axis(labelAngle=0), sort="-y"),
            y="Count:Q",
            color="Agent:N"
        )
        .properties(height=300, width=400)
    )

    st.altair_chart(chart, use_container_width=False)

else:
    st.warning("No 'Agent' column detected for this player.")
