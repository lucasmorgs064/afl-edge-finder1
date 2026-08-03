import streamlit as st
import pandas as pd
import numpy as np
import json
import os

# Set Page Configuration
st.set_page_config(
    page_title="LUCASBETS // CYBER-HUD COMMAND CENTER",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 1. ADVANCED CYBERPUNK HUD CSS WITH LUCASBETS WATERMARK & DETACHED CARDS
# -----------------------------------------------------------------------------
st.html("""
    <style>
        /* Base Dark Stadium Background + Diagonal Repeating LUCASBETS Watermark */
        .stApp {
            background: 
                /* Diagonal LUCASBETS SVG Pattern Overlay */
                url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='220' height='220' viewBox='0 0 220 220'><text x='50%' y='50%' fill='rgba(0, 255, 136, 0.035)' font-size='22' font-family='sans-serif' font-weight='900' text-anchor='middle' dominant-baseline='middle' transform='rotate(-35 110 110)'>LUCASBETS</text></svg>"),
                /* Subtle Central Green Spotlight Gradient */
                radial-gradient(circle at 50% 20%, rgba(0, 255, 136, 0.08) 0%, rgba(11, 14, 20, 0.97) 75%),
                /* Dark Stadium Backdrop */
                url("https://images.unsplash.com/photo-1508098682722-e99c43a406b2?auto=format&fit=crop&w=1920&q=80");
            background-size: 220px 220px, cover, cover;
            background-attachment: fixed;
            color: #E2E8F0;
            font-family: 'Inter', -apple-system, sans-serif;
        }

        /* Glassmorphism Hero Card */
        .hud-hero-card {
            background: rgba(18, 24, 36, 0.85);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            border: 1px solid rgba(0, 255, 136, 0.3);
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.6), inset 0 0 15px rgba(0, 255, 136, 0.05);
            margin-bottom: 25px;
            position: relative;
        }

        /* Hero Pulse Highlight for #1 Ranked Bet */
        .hero-pulse {
            border: 1px solid #00FF88 !important;
            box-shadow: 0 0 35px rgba(0, 255, 136, 0.3), inset 0 0 20px rgba(0, 255, 136, 0.12) !important;
            animation: pulse-glow 2.8s infinite alternate;
        }

        @keyframes pulse-glow {
            0% { border-color: rgba(0, 255, 136, 0.4); box-shadow: 0 0 15px rgba(0, 255, 136, 0.2); }
            100% { border-color: rgba(0, 255, 136, 1.0); box-shadow: 0 0 40px rgba(0, 255, 136, 0.45); }
        }

        /* DETACHED GRID BET CARDS */
        .bet-grid-card {
            background: rgba(18, 24, 36, 0.88);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(0, 255, 136, 0.2);
            border-radius: 14px;
            padding: 16px;
            margin-bottom: 20px;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.5);
            transition: all 0.25s ease-in-out;
            position: relative;
            overflow: hidden;
        }

        .bet-grid-card:hover {
            border-color: #00FF88;
            transform: translateY(-4px);
            box-shadow: 0 10px 28px rgba(0, 255, 136, 0.25);
        }

        .bet-rank-tag {
            position: absolute;
            top: 12px;
            right: 12px;
            background: rgba(0, 255, 136, 0.15);
            color: #00FF88;
            font-weight: 800;
            font-size: 0.75rem;
            padding: 2px 8px;
            border-radius: 6px;
            border: 1px solid rgba(0, 255, 136, 0.3);
        }

        .bet-title {
            font-size: 1.05rem;
            font-weight: 800;
            color: #FFFFFF;
            margin-top: 8px;
            margin-bottom: 4px;
            line-height: 1.3;
        }

        .bet-fixture {
            font-size: 0.8rem;
            color: #94A3B8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 12px;
        }

        .odds-badge {
            background: linear-gradient(90deg, #00FF88 0%, #00D2FF 100%);
            color: #0B0E14;
            font-weight: 900;
            font-size: 1.1rem;
            padding: 4px 10px;
            border-radius: 8px;
            display: inline-block;
        }

        .confidence-bar-bg {
            background: rgba(30, 41, 59, 0.8);
            border-radius: 6px;
            height: 8px;
            width: 100%;
            margin-top: 8px;
            overflow: hidden;
        }

        .confidence-bar-fill {
            background: linear-gradient(90deg, #00FF88, #00D2FF);
            height: 100%;
            border-radius: 6px;
        }

        /* Futuristic HUD Badge */
        .hud-badge {
            background: linear-gradient(90deg, #00FF88 0%, #00D2FF 100%);
            color: #0B0E14;
            font-weight: 900;
            padding: 5px 16px;
            border-radius: 20px;
            font-size: 0.75rem;
            letter-spacing: 1.2px;
            text-transform: uppercase;
            box-shadow: 0 0 12px rgba(0, 255, 136, 0.5);
        }

        /* Custom Metrics Container */
        [data-testid="stMetric"] {
            background: rgba(18, 24, 36, 0.88) !important;
            border: 1px solid rgba(0, 255, 136, 0.25) !important;
            border-radius: 12px !important;
            padding: 16px !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.5) !important;
        }

        [data-testid="stMetricValue"] {
            color: #00FF88 !important;
            font-family: 'Monaco', 'Courier New', monospace;
            font-weight: 800 !important;
        }

        /* Cyber Button / Controls Accent */
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
# 2. IMAGE DATABASE (PLAYERS & CLUB CRESTS)
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

PLAYER_IMAGE_DATABASE = {
    "Caleb Serong": "https://encrypted-tbn2.gstatic.com/licensed-image?q=tbn:ANd9GcQ_eGg5rGeJ6ybuBG_x1TVPeqlYGBmA_FjhV8QwEvFsq9XFCNYUjFzClJmbBr6aG0i2rcWErmGBISc09UM",
    "Marcus Bontempelli": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Marcus_Bontempelli_2019.1.jpg/800px-Marcus_Bontempelli_2019.1.jpg",
    "Lachie Neale": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d6/Lachie_Neale_2019.1.jpg/800px-Lachie_Neale_2019.1.jpg",
    "Errol Gulden": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c8/Errol_Gulden_2023.1.jpg/800px-Errol_Gulden_2023.1.jpg",
    "Josh Treacy": "https://upload.wikimedia.org/wikipedia/en/thumb/e/e0/Fremantle_FC_logo.svg/200px-Fremantle_FC_logo.svg.png",
    "Joe Daniher": "https://upload.wikimedia.org/wikipedia/en/thumb/d/d4/Brisbane_Lions_logo.svg/200px-Brisbane_Lions_logo.svg.png"
}

def get_bet_image(selection, match_str):
    for player, url in PLAYER_IMAGE_DATABASE.items():
        if player in selection:
            return url
            
    parts = match_str.split(" vs ")
    if len(parts) > 0:
        return CREST_DATABASE.get(parts[0].strip().upper(), "https://upload.wikimedia.org/wikipedia/en/thumb/e/e4/Australian_Football_League.svg/200px-Australian_Football_League.svg.png")
    return "https://upload.wikimedia.org/wikipedia/en/thumb/e/e4/Australian_Football_League.svg/200px-Australian_Football_League.svg.png"

# -----------------------------------------------------------------------------
# 3. SCORING ENGINE & DATA PIPELINE
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
    df['bet_image'] = df.apply(lambda r: get_bet_image(r['selection'], r['match']), axis=1)
    df = df.sort_values(by=['confidence_score', 'edge_%'], ascending=[False, False])
    return df

@st.cache_data(ttl=300)
def load_odds_data(file_path="data/latest_odds.json"):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                return pd.DataFrame(json.load(f))
        except Exception:
            pass
            
    return pd.DataFrame([
        {"round": 22, "match": "MEL vs FRE", "market_type": "Player Disposals", "selection": "Caleb Serong 25+ Disposals", "odds": 1.28, "projected_prob": 0.85, "hit_rate_l10": 0.90, "matchup_factor": 1.10},
        {"round": 22, "match": "WBD vs NTH", "market_type": "Player Disposals", "selection": "Marcus Bontempelli 25+ Disposals", "odds": 1.30, "projected_prob": 0.82, "hit_rate_l10": 0.85, "matchup_factor": 1.10},
        {"round": 22, "match": "BRI vs HAW", "market_type": "Player Disposals", "selection": "Lachie Neale 25+ Disposals", "odds": 1.35, "projected_prob": 0.80, "hit_rate_l10": 0.80, "matchup_factor": 1.05},
        {"round": 22, "match": "SYD vs PTA", "market_type": "Player Disposals", "selection": "Errol Gulden 25+ Disposals", "odds": 1.38, "projected_prob": 0.78, "hit_rate_l10": 0.80, "matchup_factor": 1.00},
        {"round": 22, "match": "MEL vs FRE", "market_type": "Total Goals", "selection": "Josh Treacy 2+ Goals", "odds": 1.40, "projected_prob": 0.77, "hit_rate_l10": 0.80, "matchup_factor": 1.15},
        {"round": 22, "match": "BRI vs HAW", "market_type": "Total Goals", "selection": "Joe Daniher 2+ Goals", "odds": 1.45, "projected_prob": 0.73, "hit_rate_l10": 0.70, "matchup_factor": 1.10},
        {"round": 22, "match": "MEL vs FRE", "market_type": "Head to Head", "selection": "Fremantle Win", "odds": 1.45, "projected_prob": 0.73, "hit_rate_l10": 0.75, "matchup_factor": 1.00},
    ])

# -----------------------------------------------------------------------------
# 4. DASHBOARD RENDER ENGINE
# -----------------------------------------------------------------------------
st.title("⚡ LUCASBETS // CYBER-HUD COMMAND CENTER")
st.caption("Quantum Value Analytics Engine • Sportsbet Active Markets $\\ge \\$1.20$")

df_raw = load_odds_data()
df_ranked = rank_sportsbet_markets(df_raw, min_odds=1.20)

# Sidebar Parameters
st.sidebar.header("🕹️ TERMINAL PARAMETERS")
selected_match = st.sidebar.selectbox("Match Select", ["All Round Matches"] + list(df_ranked["match"].unique()))
min_odds_val, max_odds_val = st.sidebar.slider("Odds Band ($)", 1.20, 3.00, (1.20, 2.00), 0.05)
selected_markets = st.sidebar.multiselect("Market Categories", list(df_ranked["market_type"].unique()), list(df_ranked["market_type"].unique()))
min_conf_score = st.sidebar.slider("Min Confidence Index (%)", 50.0, 95.0, 65.0, 1.0)

# Filtering logic
df_filtered = df_ranked[
    (df_ranked["odds"] >= min_odds_val) &
    (df_ranked["odds"] <= max_odds_val) &
    (df_ranked["market_type"].isin(selected_markets)) &
    (df_ranked["confidence_score"] >= min_conf_score)
].copy()

if selected_match != "All Round Matches":
    df_filtered = df_filtered[df_filtered["match"] == selected_match]

df_filtered["rank"] = range(1, len(df_filtered) + 1)

# --- HERO TOP PICK CARD ---
if not df_filtered.empty:
    top = df_filtered.iloc[0]
    
    st.markdown('<div class="hud-hero-card hero-pulse">', unsafe_allow_html=True)
    c1, c2 = st.columns([1, 2.5])
    with c1:
        st.image(top['bet_image'], use_container_width=True)
    with c2:
        st.markdown('<span class="hud-badge">⚡ LUCASBETS ALGORITHM TOP SELECTION</span>', unsafe_allow_html=True)
        st.markdown(f"## {top['selection']}")
        st.markdown(f"**Fixture:** {top['match']} | **Market:** {top['market_type']}")
        
        k1, k2, k3 = st.columns(3)
        k1.metric("Confidence Index", f"{top['confidence_score']}%")
        k2.metric("Sportsbet Odds", f"${top['odds']:.2f}")
        k3.metric("Model Edge", f"{top['edge_%']:+.2f}%")
    st.markdown('</div>', unsafe_allow_html=True)

# Metrics Grid
m1, m2, m3, m4 = st.columns(4)
m1.metric("Analyzed Markets", len(df_ranked))
m2.metric("Qualifying Picks", len(df_filtered))
m3.metric("Highest Index", f"{df_filtered['confidence_score'].max()}%" if not df_filtered.empty else "N/A")
m4.metric("Avg Value Edge", f"{df_filtered['edge_%'].mean():.2f}%" if not df_filtered.empty else "0.00%")

st.divider()

# Main Display Tabs
tab1, tab2, tab3 = st.tabs(["📊 Live Bet Matrix (Detached Grid)", "🧩 SGM Engine", "🧬 Model Blueprint"])

with tab1:
    st.subheader("High Confidence Value Selections")
    
    if df_filtered.empty:
        st.info("No market selections match current filter criteria.")
    else:
        # Render detached square/card grid in rows of 3
        cols_per_row = 3
        rows = [df_filtered.iloc[i:i + cols_per_row] for i in range(0, len(df_filtered), cols_per_row)]

        for row in rows:
            cols = st.columns(cols_per_row)
            for idx, (index, item) in enumerate(row.iterrows()):
                with cols[idx]:
                    st.markdown(f"""
                        <div class="bet-grid-card">
                            <span class="bet-rank-tag">#{item['rank']}</span>
                            <div style="text-align: center; margin-bottom: 10px;">
                                <img src="{item['bet_image']}" style="height: 90px; border-radius: 8px; object-fit: contain;">
                            </div>
                            <div class="bet-title">{item['selection']}</div>
                            <div class="bet-fixture">{item['match']} • {item['market_type']}</div>
                            
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 12px;">
                                <span class="odds-badge">${item['odds']:.2f}</span>
                                <span style="color: #00FF88; font-weight: 700; font-size: 0.9rem;">Edge: {item['edge_%']:+.2f}%</span>
                            </div>
                            
                            <div style="margin-top: 10px; font-size: 0.8rem; color: #94A3B8; display: flex; justify-content: space-between;">
                                <span>Confidence</span>
                                <span><b>{item['confidence_score']}%</b></span>
                            </div>
                            <div class="confidence-bar-bg">
                                <div class="confidence-bar-fill" style="width: {item['confidence_score']}%;"></div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

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
                st.markdown(f"<div class='hud-hero-card' style='padding:12px; margin-bottom:8px;'><b>Leg {selected_legs.index.get_loc(idx) + 1}:</b> {leg['selection']} | Odds: <b>${leg['odds']:.2f}</b> | Confidence: <b>{leg['confidence_score']}%</b></div>", unsafe_allow_html=True)

with tab3:
    st.markdown("""
    ### Lucasbets Model Evaluation Architecture
    * **Model Projected Probability (50%):** Weighted rating via Squiggle API + team projected ratings.
    * **Historical Cover Frequency (35%):** Player/Line cover rate across last 10 games.
    * **Matchup Defense Rating (15%):** Opponent concession indexes for specific key stats.
    """)
