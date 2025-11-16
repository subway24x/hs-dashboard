import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="Valorant Scrim Dashboard", layout="wide")

# Logo + title
col1, col2 = st.columns([1, 10])
with col1:
    st.image("heaven_sent_logo.png", width=70)
with col2:
    st.markdown("<h1 style='color:#d4af37;'>Valorant Scrim Dashboard</h1>", unsafe_allow_html=True)


# ---------------------------------------------------------
# DATE FILTER
# ---------------------------------------------------------
st.markdown("### 🔎 Filter by Date Range")

c1, c2 = st.columns(2)
with c1:
    start_date = st.date_input("Start Date (Overview)")
with c2:
    end_date = st.date_input("End Date (Overview)")

st.write("---")


# ---------------------------------------------------------
# MAP OVERVIEW TABLE (Example Placeholder)
# ---------------------------------------------------------

st.markdown("### 🗺️ Map Overview: Total Games, Wins, Draws, Losses, Win Rate")

map_data = pd.DataFrame({
    "Map": ["Ascent", "Fracture", "Icebox", "Lotus", "Split"],
    "Games": [10, 6, 9, 3, 4],
    "Wins": [7, 3, 6, 1, 1],
    "Draws": [2, 2, 3, 1, 1],
    "Losses": [1, 1, 0, 1, 1],
    "Win Rate": [0.70, 0.50, 0.66, 0.33, 0.25]
})

st.dataframe(map_data, use_container_width=True)
st.write("---")


# ---------------------------------------------------------
# MAP WIN RATES BAR CHART
# ---------------------------------------------------------

st.markdown("### 📊 Map Win Rates")

fig = px.bar(
    map_data,
    x="Win Rate",
    y="Map",
    orientation='h',
    text=map_data["Win Rate"].apply(lambda x: f"{x*100:.1f}%"),
    color="Win Rate",
    color_continuous_scale=["red", "orange", "yellow"]
)

fig.update_layout(
    paper_bgcolor="#0f1113",
    plot_bgcolor="#0f1113",
    font=dict(color="white"),
    showlegend=False
)

st.plotly_chart(fig, use_container_width=True)
