import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Player vs VCT Benchmark", layout="wide")
LOGO = "heaven_sent_logo.png"


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------
col1, col2 = st.columns([1, 8])
with col1:
    st.image(LOGO, width=72)
with col2:
    st.markdown("<h1 style='color:#d4af37;'>Player vs VCT Benchmark Comparison</h1>", unsafe_allow_html=True)


# ---------------------------------------------------------
# LOAD PLAYER DATA FROM SESSION STATE
# ---------------------------------------------------------
if "player_stats_df" not in st.session_state:
    st.error("⚠ Player data not loaded. Please open the Player Stats page first.")
    st.stop()

df = st.session_state["player_stats_df"].copy()


# ---------------------------------------------------------
# HELPER: FIND COLUMN BY NAMES
# ---------------------------------------------------------
def find(df, names):
    for c in df.columns:
        if c.lower() in [n.lower() for n in names]:
            return c
    for c in df.columns:
        for n in names:
            if n.lower() in c.lower():
                return c
    return None


# ---------------------------------------------------------
# DETECT SHEET COLUMNS
# ---------------------------------------------------------
player_col  = find(df, ["player", "name"])
kills_col   = find(df, ["kills"])
deaths_col  = find(df, ["deaths"])
assists_col = find(df, ["assists"])
acs_col     = find(df, ["acs"])
fk_col      = find(df, ["fk", "first kill"])

if player_col is None:
    st.error("❌ Could not detect a 'Player' column.")
    st.stop()

players = sorted(df[player_col].dropna().unique().tolist())


# ---------------------------------------------------------
# UI CONTROLS
# ---------------------------------------------------------
left, right = st.columns([2, 1])
with left:
    selected_player = st.selectbox("Select Player", players)

with right:
    selected_role = st.selectbox("Role", ["Duelist", "Controller", "Initiator", "Sentinel"])


# ---------------------------------------------------------
# FILTER FOR SELECTED PLAYER
# ---------------------------------------------------------
df_p = df[df[player_col] == selected_player].copy()

if df_p.empty:
    st.error("No stats found for this player.")
    st.stop()


# ---------------------------------------------------------
# CALCULATE PLAYER METRICS (NEW SYSTEM)
# ---------------------------------------------------------
def safe_sum(col):
    return pd.to_numeric(df_p[col], errors="coerce").fillna(0).sum() if col else 0

def safe_mean(col):
    return pd.to_numeric(df_p[col], errors="coerce").dropna().mean() if col else np.nan


# 1️⃣ Rounds = scrims × 24
scrim_count = len(df_p)
total_rounds = scrim_count * 24

# 2️⃣ Base values
total_kills   = safe_sum(kills_col)
total_assists = safe_sum(assists_col)
total_fk      = safe_sum(fk_col)

# 3️⃣ Metrics
player_acs  = safe_mean(acs_col)
player_kpr  = total_kills / total_rounds if total_rounds > 0 else np.nan
player_fkpr = total_fk / total_rounds if total_rounds > 0 else np.nan
player_kapr = (total_kills + total_assists) / total_rounds if total_rounds > 0 else np.nan

PLAYER_METRICS = {
    "ACS": player_acs,
    "KPR": player_kpr,
    "FK per Round": player_fkpr,
    "K+A per Round": player_kapr
}


# ---------------------------------------------------------
# STATIC VCT BENCHMARK SET
# ---------------------------------------------------------
VCT_BENCHMARKS = {
    "controller": {
        "ACS": 199,
        "KPR": 0.70,
        "FK per Round": 0.10,
        "K+A per Round": 0.92
    },
    "duelist": {
        "ACS": 232,
        "KPR": 0.83,
        "FK per Round": 0.18,
        "K+A per Round": 1.05
    },
    "initiator": {
        "ACS": 209,
        "KPR": 0.74,
        "FK per Round": 0.11,
        "K+A per Round": 1.06
    },
    "sentinel": {
        "ACS": 183,
        "KPR": 0.63,
        "FK per Round": 0.08,
        "K+A per Round": 0.78
    }
}

bench = VCT_BENCHMARKS[selected_role.lower()]


# ---------------------------------------------------------
# LOAD VCT BENCHMARKS
# ---------------------------------------------------------
@st.cache_data
def load_benchmarks(role):
    role = role.lower()

    benchmarks = {
        "controller": {
            "ACS": 199,
            "KPR": 0.70,
            "FK per Round": 0.10,
            "K+A per Round": 0.92
        },
        "duelist": {
            "ACS": 232,
            "KPR": 0.83,
            "FK per Round": 0.18,
            "K+A per Round": 1.05
        },
        "initiator": {
            "ACS": 209,
            "KPR": 0.74,
            "FK per Round": 0.11,
            "K+A per Round": 1.06
        },
        "sentinel": {
            "ACS": 183,
            "KPR": 0.63,
            "FK per Round": 0.08,
            "K+A per Round": 0.78
        }
    }

    return benchmarks.get(
        role,
        {"ACS": np.nan, "KPR": np.nan, "FK per Round": np.nan, "K+A per Round": np.nan}
    )

# ---------------------------------------------------------
# NORMALIZE VALUES (THIS FIXES THE RADAR CHART)
# ---------------------------------------------------------

metrics = list(PLAYER_METRICS.keys())

player_vals_raw = [PLAYER_METRICS[m] for m in metrics]
bench_vals_raw = [bench[m] for m in metrics]

# Avoid division errors
def norm(p, b):
    if b is None or b == 0 or b == np.nan:
        return 0
    return p / b

player_vals = [norm(player_vals_raw[i], bench_vals_raw[i]) for i in range(len(metrics))]
bench_vals = [1 for _ in metrics]   # VCT benchmark becomes a perfect 1.0 shape

# ---------------------------------------------------------
# RADAR CHART (Ominous 1:1 Style - FIXED)
# ---------------------------------------------------------
fig = go.Figure()

# --- VCT Benchmark polygon ---
fig.add_trace(go.Scatterpolar(
    r=bench_vals,
    theta=metrics,
    name=f"VCT {selected_role} Avg",
    line=dict(color="rgba(130,130,130,0.9)", width=3),
    fill='toself',
    fillcolor="rgba(100,100,100,0.35)"
))

# --- Player polygon ---
fig.add_trace(go.Scatterpolar(
    r=player_vals,
    theta=metrics,
    name=selected_player,
    line=dict(color="rgba(212,175,55,1)", width=3),
    fill='toself',
    fillcolor="rgba(212,175,55,0.45)"
))

# --- Layout styling ---
fig.update_layout(
    polar=dict(
        bgcolor="#0f1113",
        radialaxis=dict(
            visible=True,
            range=[0, 1],
            tickvals=[0, 0.25, 0.50, 0.75, 1.00],
            tickfont=dict(size=12, color="rgba(255,255,255,0.5)"),
            gridcolor="rgba(255,255,255,0.06)",
            linecolor="rgba(255,255,255,0.08)"
        ),
        angularaxis=dict(
            tickfont=dict(size=15, color="#d4af37"),
            gridcolor="rgba(255,255,255,0.08)",
            linecolor="rgba(255,255,255,0.08)"
        )
    ),
    showlegend=True,
    legend=dict(
        font=dict(color="white", size=13),
        bgcolor="rgba(0,0,0,0)"
    ),
    paper_bgcolor="#0f1113",
    plot_bgcolor="#0f1113",
    margin=dict(l=60, r=60, t=60, b=60)
)

st.plotly_chart(fig, use_container_width=True)



# ---------------------------------------------------------
# DATA TABLE + DOWNLOAD
# ---------------------------------------------------------
comp_df = pd.DataFrame({
    "Metric": metrics,
    "Player": player_vals,
    "VCT Bench": bench_vals
})
comp_df["Delta"] = comp_df["Player"] - comp_df["VCT Bench"]

st.subheader("Full Numeric Comparison")
st.dataframe(
    comp_df.style.format({"Player": "{:.2f}", "VCT Bench": "{:.2f}", "Delta": "{:.2f}"}),
    use_container_width=True
)

st.download_button(
    "Download CSV",
    comp_df.to_csv(index=False),
    file_name=f"{selected_player}_benchmark.csv",
    mime="text/csv"
)
