import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
import html
import requests

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="HS Composition Stats", layout="wide")

LOGO = "heaven_sent_logo.png"

# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------
col1, col2 = st.columns([1, 8])
with col1:
    st.image(LOGO, width=90)
with col2:
    st.markdown(
        "<h1 style='color:#d4af37;'>Composition Statistics</h1>",
        unsafe_allow_html=True
    )

def render():
    st.header("Composition Statistics")
# ---------------------------------------------------------
# AGENT ICONS (LIVE FROM VALORANT API)
# ---------------------------------------------------------
@st.cache_data
def load_agent_icons():
    url = "https://valorant-api.com/v1/agents?isPlayableCharacter=true"
    data = requests.get(url).json()

    mapping = {}
    for agent in data["data"]:
        mapping[agent["displayName"]] = agent["displayIcon"]

    return mapping

AGENT_ICONS = load_agent_icons()


def comp_to_icons(comp):
    agents = [a.strip() for a in comp.replace("|", ",").split(",")]
    html_icons = ""

    for a in agents:
        if a in AGENT_ICONS:
            html_icons += f"<img src='{AGENT_ICONS[a]}' width='28' style='margin-right:3px;'>"
        else:
            html_icons += f"<span style='color:white;margin-right:4px'>{html.escape(a)}</span>"
    return html_icons


# ---------------------------------------------------------
# GOOGLE SHEETS LOAD
# ---------------------------------------------------------
SPREADSHEET_NAME = "HS SPREADSHEET NEW ROSTER"

@st.cache_data
def load_comp_sheet():
    try:
        service_info = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(service_info, scope)
        client = gspread.authorize(creds)

        sheet = client.open(SPREADSHEET_NAME).worksheet("Comp Stats")
        raw = sheet.get_all_values()

        row1 = [x.strip() for x in raw[0]]
        row3 = [x.strip() for x in raw[2]]

        final_headers = []
        for h1, h3 in zip(row1, row3):
            final_headers.append(h3 if h3 else h1 if h1 else "Unknown")

        df = pd.DataFrame(raw[3:], columns=final_headers)

        df = df.apply(lambda col: col.str.strip()
                      if col.dtype == "object" else col)

        # Convert numeric columns
        numeric_cols = ["ATK W", "ATK L", "DEF W", "DEF L"]
        for c in numeric_cols:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

        return df

    except Exception as e:
        st.error(f"Error loading Comp Stats sheet: {e}")
        return None


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------
df = load_comp_sheet()
if df is None:
    st.stop()

# Detect agent columns
agent_cols = sorted([c for c in df.columns if "agent" in c.lower()])


def build_comp(row):
    return " | ".join([row[c] for c in agent_cols if row.get(c, "").strip() != ""])


df["Comp"] = df.apply(build_comp, axis=1)

# Map list
map_col = "Map"
result_col = "Result"

maps = sorted(df[map_col].unique())

selected_map = st.selectbox("Select Map", maps)

df_map = df[df[map_col] == selected_map]

# ---------------------------------------------------------
# MAIN COMPOSITION STATS (EXPANDED)
# ---------------------------------------------------------
comp_stats = (
    df_map.groupby("Comp")
    .agg(
        Games=("Comp", "count"),
        Wins=(result_col, lambda x: (x == "Win").sum()),
        Losses=(result_col, lambda x: (x == "Loss").sum()),
        Ties=(result_col, lambda x: (x == "Tie").sum()),
        ATK_W=("ATK W", "sum"),
        ATK_L=("ATK L", "sum"),
        DEF_W=("DEF W", "sum"),
        DEF_L=("DEF L", "sum")
    )
    .reset_index()
)

# Win rates
comp_stats["Win Rate"] = (comp_stats["Wins"] / comp_stats["Games"]) * 100
comp_stats["ATK WR"] = comp_stats["ATK_W"] / \
    (comp_stats["ATK_W"] + comp_stats["ATK_L"] + 1e-9) * 100
comp_stats["DEF WR"] = comp_stats["DEF_W"] / \
    (comp_stats["DEF_W"] + comp_stats["DEF_L"] + 1e-9) * 100

# Side bias
comp_stats["Side Bias"] = comp_stats["ATK WR"] - comp_stats["DEF WR"]

# Round differential
comp_stats["Round Diff"] = (comp_stats["ATK_W"] + comp_stats["DEF_W"]) - \
    (comp_stats["ATK_L"] + comp_stats["DEF_L"])

# Strength score
comp_stats["Strength Score"] = (
    comp_stats["Win Rate"] * 0.7 +
    ((comp_stats["Games"] / df_map.shape[0]) * 100) * 0.3
)

# ---------------------------------------------------------
# VISUAL DISPLAY WITH ICONS (FINAL FIX)
# ---------------------------------------------------------
st.markdown(f"<h2 style='color:#d4af37;'>Top Compositions on {selected_map}</h2>", unsafe_allow_html=True)

if comp_stats.empty:
    st.warning("No compositions for this map.")
else:
    for _, row in comp_stats.sort_values("Win Rate", ascending=False).iterrows():

        icons_html = comp_to_icons(row["Comp"])
        winrate = float(row["Win Rate"])

        html_lines = [
            "<div style='display:flex; align-items:center; margin-bottom:18px;'>",

            # ICONS
            f"<div style='width:260px;'>{icons_html}</div>",

            # BAR
            "<div style='flex-grow:1; margin:0 12px;'>",
            "<div style='background:#252525; height:14px; border-radius:7px;'>",
            f"<div style='width:{winrate}%; background:#d4af37; height:14px; border-radius:7px;'></div>",
            "</div>",
            "</div>",

            # LABEL
            f"<div style='color:white; width:75px; text-align:right;'>{winrate:.1f}%</div>",

            "</div>"
        ]

        html_block = "\n".join(html_lines)
        st.markdown(html_block, unsafe_allow_html=True)






# ---------------------------------------------------------
# PICK RATE PER MAP
# ---------------------------------------------------------
st.markdown(
    "<h3 style='color:#d4af37;'>Composition Pick Rate</h3>",
    unsafe_allow_html=True
)

pick_rate = comp_stats.copy()
pick_rate["Pick Rate %"] = (pick_rate["Games"] / df_map.shape[0]) * 100

fig = px.bar(
    pick_rate.sort_values("Pick Rate %", ascending=False),
    x="Comp", y="Pick Rate %",
    labels={'Comp': 'Composition'},
    text_auto=".1f"
)
st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
# AGENT FREQUENCY CHART
# ---------------------------------------------------------
st.markdown(
    "<h3 style='color:#d4af37;'>Agent Frequency on This Map</h3>",
    unsafe_allow_html=True
)

agent_list = []

for comp in df_map["Comp"]:
    for agent in comp.split("|"):
        agent_list.append(agent.strip())

agent_freq = pd.Series(agent_list).value_counts().reset_index()
agent_freq.columns = ["Agent", "Count"]

fig2 = px.bar(agent_freq, x="Agent", y="Count", text_auto=True)
st.plotly_chart(fig2, use_container_width=True)

# ---------------------------------------------------------
# FULL DATA TABLE
# ---------------------------------------------------------
st.markdown("<h3 style='color:#d4af37;'>Full Composition Breakdown</h3>",
            unsafe_allow_html=True)

display_cols = [
    "Comp", "Games", "Wins", "Losses", "Win Rate",
    "ATK WR", "DEF WR", "Side Bias", "Round Diff",
    "Strength Score"
]

st.dataframe(comp_stats[display_cols].style.format({
    "Win Rate": "{:.1f}%",
    "ATK WR": "{:.1f}%",
    "DEF WR": "{:.1f}%",
    "Side Bias": "{:.1f}",
    "Strength Score": "{:.1f}"
}), use_container_width=True)

