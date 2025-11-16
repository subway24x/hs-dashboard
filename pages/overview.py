import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
import os

st.set_page_config(page_title="Overview — Map Performance", layout="wide")

# =========================
# THEME COLORS
# =========================
BG = "#0d0f12"
CARD = "#16181d"
GOLD = "#d4af37"
RED = "#ff4d4d"
ORANGE = "#ff9933"
YELLOW = "#f7d774"

# =========================
# SAFE LOGO LOADER
# =========================
def safe_logo_display():
    logo_path = "heaven_sent_logo.png"   # <<<< FIXED

    if os.path.exists(logo_path):
        st.image(logo_path, width=110)
    else:
        st.markdown(
            f"""
            <div style='background:{CARD}; padding:20px; border-radius:10px;
            border:1px solid {GOLD}; text-align:center;'>
                <p style='color:{GOLD}; font-size:18px;'>
                    ⚠️ Logo file missing: <b>{logo_path}</b>
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

# =========================
# HEADER
# =========================
col_l, col_r = st.columns([1, 6])
with col_l:
    safe_logo_display()

with col_r:
    st.markdown(
        f"<h1 style='color:{GOLD}; font-weight:800;'>Overview — Map Performance</h1>",
        unsafe_allow_html=True
    )

# =========================
# LOAD GOOGLE SHEET — AUTO HEADER DETECTION
# =========================
def load_map_wl_rate():
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            "service_account.json", scope
        )
        client = gspread.authorize(creds)

        sheet = client.open("HS SPREADSHEET NEW ROSTER").worksheet("Map W/L Rate")
        raw = sheet.get_all_values()

        # -------- auto-detect header row (first row containing "Maps") --------
        header_row_index = None
        for i, row in enumerate(raw):
            if any(str(cell).strip().lower() == "maps" for cell in row):
                header_row_index = i
                break

        if header_row_index is None:
            raise Exception("Could not find a 'Maps' header in any row.")

        headers = raw[header_row_index]
        data = raw[header_row_index + 1 :]

        df = pd.DataFrame(data, columns=headers)

        # --- UNIVERSAL-SAFE COLUMN DEDUPE ---
        def dedupe_columns(cols):
            seen = {}
            new_cols = []
            for c in cols:
                if c not in seen:
                    seen[c] = 0
                    new_cols.append(c)
                else:
                    seen[c] += 1
                    new_cols.append(f"{c}.{seen[c]}")
            return new_cols

        df.columns = dedupe_columns(df.columns)

        # drop empty columns
        df = df.loc[:, df.columns.notnull()]
        df = df.loc[:, df.columns != ""]

        # locate actual 'Maps' column (even if renamed 'Maps.1')
        maps_col = None
        for c in df.columns:
            if c.strip().lower() == "maps":
                maps_col = c
                break

        if maps_col is None:
            raise Exception("No usable Maps column found, even after dedupe.")

        df = df[df[maps_col].notna() & (df[maps_col] != "")]

        # convert numeric columns
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="ignore")

        return df

    except Exception as e:
        st.error(f"❌ Error loading Map W/L Rate sheet: {e}")
        return None




df = load_map_wl_rate()
if df is None:
    st.stop()

st.success("✅ Map W/L Rate loaded successfully!")

# =========================
# RAW TABLE
# =========================
st.markdown(f"<h3 style='color:{GOLD}; margin-top:25px;'>Raw Data</h3>", unsafe_allow_html=True)
st.dataframe(df, use_container_width=True, height=350)

# =========================
# SELECT MAP
# =========================
st.markdown("---")

map_options = df["Maps"].unique()
selected_map = st.selectbox("Select Map:", map_options)

row = df[df["Maps"] == selected_map].iloc[0]

# =========================
# STAT CARDS
# =========================
st.markdown(
    f"<h3 style='color:{GOLD}; margin-top:20px;'>📍 Performance for {selected_map}</h3>",
    unsafe_allow_html=True,
)

def card(col, title, value):
    col.markdown(
        f"""
        <div style='background:{CARD}; padding:18px; border-radius:12px;'>
            <p style='color:{GOLD}; margin:0; font-size:16px; font-weight:600;'>{title}</p>
            <p style='color:white; margin:0; font-size:30px; font-weight:800;'>{value}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

top1, top2, top3, top4 = st.columns(4)
card(top1, "Total Games Played", int(row["Total Games Played"]))
card(top2, "Map Win %", f"{row['Map Win%']:.2f}%")
card(top3, "Atk Win %", f"{row['Atk Win%']:.2f}%")
card(top4, "Def Win %", f"{row['Def Win%']:.2f}%")

bot1, bot2 = st.columns(2)
card(bot1, "Pistol Win % (ATK)", f"{row['Pistol Win% (ATK)']:.2f}%")
card(bot2, "Pistol Win % (DEF)", f"{row['Pistol Win% (DEF)']:.2f}%")

# =========================
# MAP WIN RATE BAR GRAPH
# =========================
st.markdown(
    f"<h3 style='color:{GOLD}; margin-top:35px;'>📊 Map Win Rates</h3>",
    unsafe_allow_html=True,
)

chart_df = df[["Maps", "Map Win%"]].sort_values("Map Win%", ascending=True)

fig = px.bar(
    chart_df,
    x="Map Win%",
    y="Maps",
    orientation="h",
    text="Map Win%",
    color="Map Win%",
    color_continuous_scale=[RED, ORANGE, YELLOW, GOLD],
)

fig.update_layout(
    plot_bgcolor=BG,
    paper_bgcolor=BG,
    font=dict(color="white", size=14),
    coloraxis_showscale=False,
)

fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")

st.plotly_chart(fig, use_container_width=True)
