import streamlit as st
import pandas as pd
import numpy as np
import json
import os

# Page Config
st.set_page_config(
    page_title="AFL CYBER-HUD // COMMAND CENTER",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 1. NEXT-GEN CYBERPUNK HUD CSS WITH AFL STADIUM BACKGROUND & OVAL GRID
# -----------------------------------------------------------------------------
st.html("""
    <style>
        /* Dark Cyber Stadium Background with Subtle AFL Oval Field Grid Pattern */
        .stApp {
            background: 
                radial-gradient(circle at 50% 20%, rgba(0, 255, 136, 0.08) 0%, rgba(11, 14, 20, 0.95) 70%),
                url("https://images.unsplash.com/photo-1508098682722-e99c43a406b2?auto=format&fit=crop&w=1920&q=80");
            background-size: cover;
            background-attachment: fixed;
            color: #E2E8F0;
            font-family: 'Inter', -apple-system, sans-serif;
        }

        /* Glassmorphism Containers with Neon Glow Borders */
        .hud-card {
            background: rgba(18, 24, 36, 0.75);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(0, 255, 136, 0.25);
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5), inset 0 0 15px rgba(0, 255, 136, 0.05);
            margin-bottom: 25px;
            position: relative;
            overflow: hidden;
        }

        /* Hero Pulse Highlight for Top-Ranked Pick */
        .hero-pulse {
            border: 1px solid #00FF88 !important;
            box-shadow: 0 0 30px rgba(0, 255, 136, 0.25), inset 0 0 20px rgba(0, 255, 136, 0.1) !important;
            animation: pulse-glow 3s infinite alternate;
        }

        @keyframes pulse-glow {
            0% { border-color: rgba(0, 255, 136, 0.4); box-shadow: 0 0 15px rgba(0, 255, 136, 0.2); }
            100% { border-color: rgba(0, 255, 136, 1.0); box-shadow: 0 0 35px rgba(0, 255, 136, 0.4); }
        }

        /* Futuristic HUD Badge */
        .hud-badge {
            background: linear-gradient(90deg, #00FF88 0%, #00D2FF 100%);
            color: #0B0E14;
            font-weight: 900;
            padding: 4px 14px;
            border-radius: 20px;
            font-size: 0.75rem;
            letter-spacing: 1px;
            text-transform: uppercase;
            box-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
        }

        /* Custom Metrics Styling */
        [data-testid="stMetric"] {
            background: rgba(18, 24, 36, 0.85) !important;
            border: 1px solid rgba(0, 255, 136, 0.2) !important;
            border-radius: 12px !important;
            padding: 16px !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.4) !important;
        }

        [data-testid="stMetricValue"] {
            color: #00FF88 !important;
            font-family: 'Monaco', 'Courier New', monospace;
            font-weight: 800 !important;
        }

        /* Custom Table HUD Frame */
        .stDataFrame {
            border: 1px solid rgba(0, 255, 136, 0.3) !important;
            border-radius: 12px !important;
            background: rgba(11, 14, 20, 0.85) !important;
            backdrop-filter: blur(8px) !important;
        }

        /* Cyber Button / Accent Styling */
        .stButton>button {
            background: linear-gradient(90deg, #00FF88 0%, #00D2FF 100%) !important;
            color: #0B0E14 !important;
            font-weight: 800 !important;
            border: none !important;
            border-radius: 8px !important;
            text-transform: uppercase !important;
            letter-spacing: 1px !important;
        }
    </style>
""")

# -----------------------------------------------------------------------------
# 2. Team Crest & Player Image Database
# -----------------------------------------------------------------------------
CREST_DATABASE = {
    "ADE": "https://upload.wikimedia.org/wikipedia/en/thumb/8/84/Adelaide_Crows_logo.svg/200px-Adelaide_Crows_logo.svg.png",
    "BRI": "https://upload.wikimedia.org/wikipedia/en/thumb/d/d4/Brisbane_Lions_logo.svg/200px-Brisbane_Lions_logo.svg.png",
    "CAR": "https://upload.wikimedia.org/wikipedia/en/thumb/5/5a/Carlton_FC_logo.svg/200px-Carlton_FC_logo.svg.png",
    "COL": "https://upload.wikimedia.org/wikipedia/en/thumb/3/3d/Collingwood_FC_logo.svg/200px-Collingwood_FC_logo.svg.png",
    "ESS": "https://upload.wikimedia.org/wikipedia/en/thumb/c/c9/Essendon_FC_logo.svg/200px-Essendon_FC_logo.svg.png",
    "FRE": "https://upload.wikimedia.org/wikipedia/en/thumb/e/e0/Fremantle_FC_logo.svg/200px-Fremantle_FC_logo.svg.png",
    "GEE": "https://upload.wikimedia.org/wikipedia/en/thumb/1/10/Geelong_Cats_logo.svg/200px-Geelong_Cats_logo.svg.png",
    "GCS": "https://upload.wikimedia.org/wikipedia/en/thumb/1/16/Gold_Coast_Suns_logo.svg/200px-Gold_Coast_Suns_logo.svg.png",
    "GWS": "https://upload.wikimedia.org/wikipedia/en/thumb/d/d8/GWS_Giants_logo.svg/200px-GWS_Giants_logo.svg.png",
    "HAW": "https://upload.wikimedia.org/wikipedia/en/thumb/1/15/Hawthorn_FC_logo.svg/200px-Hawthorn_FC_logo.svg.png",
    "MEL": "https://upload.wikimedia.org/wikipedia/en/thumb/2/2f/Melbourne_FC_logo.svg/200px-Melbourne_FC_logo.svg.png",
    "NTH": "https://upload.wikimedia.org/wikipedia/en/thumb/9/91/North_Melbourne_FC_logo.svg/200px-North_Melbourne_FC_logo.svg.png",
    "PTA": "https://upload.wikimedia.org/wikipedia/en/thumb/7/77/Port_Adelaide_FC_logo.svg/200px-Port_Adelaide_FC_logo.svg.png",
    "RIC": "https://upload.wikimedia.org/wikipedia/en/thumb/1/18/Richmond_FC_logo.svg/200px-Richmond_FC_logo.svg.png",
    "STK": "https://upload.wikimedia.org/wikipedia/en/thumb/1/1c/St_Kilda_FC_logo.svg/200px-St_Kilda_FC_logo.svg.png",
    "SYD": "https://upload.wikimedia.org/wikipedia/en/thumb/e/e0/Sydney_Swans_logo.svg/200px-Sydney_Swans_logo.svg.png",
    "WCE": "https://upload.wikimedia.org/wikipedia/en/thumb/1/10/West_Coast_Eagles_logo.svg/200px-West_Coast_Eagles_logo.svg.png",
    "WBD": "https://upload.wikimedia.org/wikipedia/en/thumb/8/87/Western_Bulldogs_logo.svg/200px-Western_Bulldogs_logo.svg.png"
}

IMAGE_DATABASE = {
    "Caleb Serong": "https://encrypted-tbn2.gstatic.com/licensed-image?q=tbn:ANd9GcQ_eGg5rGeJ6ybuBG_x1TVPeqlYGBmA_FjhV8QwEvFsq9XFCNYUjFzClJmbBr6aG0i2rcWErmGBISc09UM",
    "Marcus Bontempelli": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Marcus_Bontempelli_2019.1.jpg/800px-Marcus_Bontempelli_2019.1.jpg",
    "Fremantle": "https://upload.wikimedia.org/wikipedia/en/thumb/e/e0/Fremantle_FC_logo.svg/1200px-Fremantle_FC_logo.svg.png",
    "Western Bulldogs": "https://upload.wikimedia.org/wikipedia/en/thumb/8/87/Western_Bulldogs_logo.svg/1200px-Western_Bulldogs_logo.svg.png"
}

def get_crest_url(match_str):
    parts = match_str.split(" vs ")
    if len(parts) > 0:
        return CREST_DATABASE.get(parts[0].strip().upper(), "https://upload.wikimedia.org/wikipedia/en/thumb/e/e4/Australian_Football_League.svg/200px-Australian_Football_League.svg.png")
    return "https://upload.wikimedia.org/wikipedia/en/thumb/e/e4/Australian_Football_League.svg/200px-Australian_Football_League.svg.png"

def get_hero_img(selection):
    for entity, url in IMAGE_DATABASE.items():
        if entity in selection:
            return url
    return "https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?auto=format&fit=crop&w=800&q=80"

# -----------------------------------------------------------------------------
# 3. Model Scoring Pipeline
# -----------------------------------------------------------------------------
def calculate_implied_prob(odds):
    return 1 / odds if odds > 0 else 0

def calculate_confidence_score(row):
    proj_prob = row['projected_prob']
    hit_rate = row.get('hit_rate_l10', proj_prob)
    matchup = row.get('matchup_factor', 1.0)
    
    raw_score = (0.50 * proj_prob) + (0.35 * hit_rate) + (0.15 * (proj_prob * matchup))
    implied_prob = calculate_implied_prob(row['odds'])
    edge = proj_prob - implied_prob
    
    final_confidence = np.clip(raw_score * (1 + (edge * 0.5)), 0, 1)
    return round(final_confidence * 100, 1)

def rank_sportsbet_markets(markets_df, min_odds=1.20):
    df = markets_df[markets_df['odds'] >= min_odds].copy()
    df['implied_prob'] = df['odds'].apply(calculate_implied_prob)
    df['edge_%'] = ((df['projected_prob'] - df['implied_prob']) * 100).round(2)
    df['confidence_score'] = df.apply(calculate_confidence_score, axis=1)
    df['crest_url'] = df['match'].apply(get_crest_url)
    df = df.sort_values(by=['confidence_score', 'edge_%'], ascending=[False, False])
    return df

# Data Loader
@st.cache_data(ttl=300)
def load_odds_data(file_path="data/latest_odds.json"):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                return pd.DataFrame(json.load(f))
        except Exception:
            pass
            
    # Mock Current Round Data
    return pd.DataFrame([
        {"round": 22, "match": "MEL vs FRE", "market_type": "Player Disposals", "selection": "Caleb Serong 25+ Disposals", "odds": 1.28, "projected_prob": 0.85, "hit_rate_l10": 0.90, "matchup_factor": 1.10},
        {"round": 22, "match": "WBD vs NTH", "market_type": "Player Disposals", "selection": "Marcus Bontempelli 25+ Disposals", "odds": 1.30, "projected_prob": 0.82, "hit_rate_l10": 0.85, "matchup_factor": 1.10},
        {"round": 22, "match": "MEL vs FRE", "market_type": "Total Goals", "selection": "Josh Treacy 2+ Goals", "odds": 1.40, "projected_prob": 0.77, "hit_rate_l10": 0.80, "matchup_factor": 1.15},
        {"round": 22, "match": "MEL vs FRE", "market_type": "Head to Head", "selection": "Fremantle Win", "odds": 1.45, "projected_prob": 0.73, "hit_rate_l10": 0.75, "matchup_factor": 1.00},
        {"round": 22, "match": "BRI vs HAW", "market_type": "Player Disposals", "selection": "Lachie Neale 25+ Disposals", "odds": 1.35, "projected_prob": 0.80, "hit_rate_l10": 0.80, "matchup_factor": 1.05},
        {"round": 22, "match": "SYD vs PTA", "market_type": "Player Disposals", "selection": "Errol Gulden 25+ Disposals", "odds": 1.38, "projected_prob": 0.78, "hit_rate_l10": 0.80, "matchup_factor": 1.00},
    ])

# -----------------------------------------------------------------------------
# 4. App UI Engine
# -----------------------------------------------------------------------------
st.title("⚡ AFL CYBER-HUD // COMMAND CENTER")
st.caption("Quantum Value Analytics Engine • Sportsbet Active Markets $\\ge \\$1.20$")

df_raw = load_odds_data()
df_ranked = rank_sportsbet_markets(df_raw, min_odds=1.20)

# Sidebar
st.sidebar.header("🕹️ HUD PARAMETERS")
selected_match = st.sidebar.selectbox("Match Select", ["All Round Matches"] + list(df_ranked["match"].unique()))
min_odds_val, max_odds_val = st.sidebar.slider("Odds Band ($)", 1.20, 3.00, (1.20, 2.00), 0.05)
selected_markets = st.sidebar.multiselect("Market Categories", list(df_ranked["market_type"].unique()), list(df_ranked["market_type"].unique()))
min_conf_score = st.sidebar.slider("Min Confidence Index (%)", 50.0, 95.0, 65.0, 1.0)

# Filtering
df_filtered = df_ranked[
    (df_ranked["odds"] >= min_odds_val) &
    (df_ranked["odds"] <= max_odds_val) &
    (df_ranked["market_type"].isin(selected_markets)) &
    (df_ranked["confidence_score"] >= min_conf_score)
].copy()

if selected_match != "All Round Matches":
    df_filtered = df_filtered[df_filtered["match"] == selected_match]

df_filtered["rank"] = range(1, len(df_filtered) + 1)

# --- HERO PICK (APPLY PULSE EFFECT) ---
if not df_filtered.empty:
    top = df_filtered.iloc[0]
    hero_img = get_hero_img(top['selection'])
    
    st.markdown('<div class="hud-card hero-pulse">', unsafe_allow_html=True)
    c1, c2 = st.columns([1, 2.5])
    with c1:
        st.image(hero_img, use_container_width=True)
    with c2:
        st.markdown('<span class="hud-badge">⚡ ALGORITHM TOP CONFIDENCE SELECTION</span>', unsafe_allow_html=True)
        st.markdown(f"## {top['selection']}")
        st.markdown(f"**Fixture:** {top['match']} | **Market:** {top['market_type']}")
        
        k1, k2, k3 = st.columns(3)
        k1.metric("Confidence Index", f"{top['confidence_score']}%")
        k2.metric("Sportsbet Odds", f"${top['odds']:.2f}")
        k3.metric("Model Edge", f"{top['edge_%']:+.2f}%")
    st.markdown('</div>', unsafe_allow_html=True)

# HUD Metrics Panel
m1, m2, m3, m4 = st.columns(4)
m1.metric("Analyzed Markets", len(df_ranked))
m2.metric("Qualifying Picks", len(df_filtered))
m3.metric("Highest Index", f"{df_filtered['confidence_score'].max()}%" if not df_filtered.empty else "N/A")
m4.metric("Avg Value Edge", f"{df_filtered['edge_%'].mean():.2f}%" if not df_filtered.empty else "0.00%")

st.divider()

# Main Matrix & SGM Tabs
tab1, tab2, tab3 = st.tabs(["📊 Live Value Matrix", "🧩 SGM Engine", "🧬 Model Blueprint"])

with tab1:
    st.subheader("Interactive Value Matrix (Odds $\\ge \\$1.20$)")
    if df_filtered.empty:
        st.info("No market selections match current filter criteria.")
    else:
        st.dataframe(
            df_filtered[['rank', 'crest_url', 'match', 'market_type', 'selection', 'odds', 'confidence_score', 'edge_%']],
            column_config={
                "rank": st.column_config.NumberColumn("Rank", format="#%d"),
                "crest_url": st.column_config.ImageColumn("Crest", help="Team Crest Logo"),
                "match": "Fixture",
                "market_type": "Market",
                "selection": "Selection Name",
                "odds": st.column_config.NumberColumn("Odds", format="$%.2f"),
                "confidence_score": st.column_config.ProgressColumn("Confidence Index", format="%.1f%%", min_value=0, max_value=100),
                "edge_%": st.column_config.NumberColumn("Model Edge", format="%+.2f%%"),
            },
            hide_index=True,
            use_container_width=True
        )

with tab2:
    st.subheader("Cyber Multi Builder")
    col_s1, col_s2 = st.columns([1, 2])
    with col_s1:
        sgm_match = st.selectbox("Target Match", [m for m in list(df_ranked["match"].unique())])
        num_legs = st.slider("Number of Legs", 2, 4, 2)
    with col_s2:
        sgm_pool = df_ranked[(df_ranked["match"] == sgm_match) & (df_ranked["confidence_score"] >= 70.0)]
        if len(sgm_pool) < num_legs:
            st.warning(f"Insufficient high-confidence legs to assemble multi for {sgm_match}.")
        else:
            selected_legs = sgm_pool.head(num_legs)
            raw_multi = 1.0
            for o in selected_legs["odds"]:
                raw_multi *= o
            st.markdown(f"### Target Multi Odds: **${(raw_multi * 0.92):.2f}**")
            for idx, leg in selected_legs.iterrows():
                st.markdown(f"<div class='hud-card' style='padding:12px; margin-bottom:8px;'><b>Leg {selected_legs.index.get_loc(idx) + 1}:</b> {leg['selection']} | Odds: <b>${leg['odds']:.2f}</b> | Confidence: <b>{leg['confidence_score']}%</b></div>", unsafe_allow_html=True)

with tab3:
    st.markdown("""
    ### Quantum Evaluation Engine
    * **Model Projected Probability (50%):** Weighted rating via Squiggle API + team projected ratings.
    * **Historical Cover Rate (35%):** Player/Line cover frequency across last 10 games.
    * **Matchup Defense Rating (15%):** Opponent concession indexes for specific key stats.
    """)
