import streamlit as st
import pandas as pd
import numpy as np
import json
import os

# Set Page Configuration
st.set_page_config(
    page_title="LUCASBETS // SPORTS CARD TERMINAL",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 1. ADVANCED CYBERPUNK CSS: DIAGONAL WATERMARK & TRADING SPORTS CARDS
# -----------------------------------------------------------------------------
st.html("""
    <style>
        /* Base Dark Stadium Background + Diagonal Repeating LUCASBETS Watermark */
        .stApp {
            background: 
                /* Diagonal LUCASBETS SVG Pattern Overlay */
                url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='220' height='220' viewBox='0 0 220 220'><text x='50%' y='50%' fill='rgba(0, 255, 136, 0.035)' font-size='22' font-family='sans-serif' font-weight='900' text-anchor='middle' dominant-baseline='middle' transform='rotate(-35 110 110)'>LUCASBETS</text></svg>"),
                /* Central Glow Gradient */
                radial-gradient(circle at 50% 20%, rgba(0, 255, 136, 0.08) 0%, rgba(11, 14, 20, 0.97) 75%),
                /* Dark Stadium Backdrop */
                url("https://images.unsplash.com/photo-1508098682722-e99c43a406b2?auto=format&fit=crop&w=1920&q=80");
            background-size: 220px 220px, cover, cover;
            background-attachment: fixed;
            color: #E2E8F0;
            font-family: 'Inter', -apple-system, sans-serif;
        }

        /* DIGITAL TRADING SPORTS CARD STYLING */
        .sports-card {
            background: linear-gradient(145deg, rgba(20, 28, 42, 0.9) 0%, rgba(10, 14, 22, 0.95) 100%);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(0, 255, 136, 0.25);
            border-radius: 18px;
            padding: 16px;
            margin-bottom: 22px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6), inset 0 0 12px rgba(0, 255, 136, 0.04);
            transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
            position: relative;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            justify: space-between;
        }

        .sports-card:hover {
            border-color: #00FF88;
            transform: translateY(-6px) scale(1.02);
            box-shadow: 0 14px 35px rgba(0, 255, 136, 0.3);
        }

        /* Top Ranked Card Special Aura */
        .rank-1-card {
            border: 1.5px solid #00FF88 !important;
            box-shadow: 0 0 25px rgba(0, 255, 136, 0.25) !important;
        }

        /* Card Image Box */
        .card-img-wrapper {
            position: relative;
            width: 100%;
            height: 140px;
            border-radius: 12px;
            overflow: hidden;
            background: radial-gradient(circle at center, rgba(0,255,136,0.15) 0%, rgba(15,23,42,0.6) 100%);
            border: 1px solid rgba(255, 255, 255, 0.08);
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .card-img-wrapper img {
            max-height: 100%;
            max-width: 100%;
            object-fit: contain;
            filter: drop-shadow(0px 5px 10px rgba(0, 0, 0, 0.7));
        }

        /* Badges & Tags */
        .card-rank-badge {
            position: absolute;
            top: 8px;
            left: 8px;
            background: rgba(11, 14, 20, 0.85);
            color: #00FF88;
            font-weight: 900;
            font-size: 0.75rem;
            padding: 3px 8px;
            border-radius: 8px;
            border: 1px solid rgba(0, 255, 136, 0.4);
            backdrop-filter: blur(4px);
        }

        .card-match-badge {
            position: absolute;
            top: 8px;
            right: 8px;
            background: rgba(11, 14, 20, 0.85);
            color: #94A3B8;
            font-weight: 700;
            font-size: 0.7rem;
            padding: 3px 8px;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            text-transform: uppercase;
        }

        /* Content Text */
        .card-title {
            font-size: 1.1rem;
            font-weight: 900;
            color: #FFFFFF;
            letter-spacing: -0.2px;
            margin-bottom: 8px;
            line-height: 1.25;
            min-height: 2.5rem;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        /* Stats Row */
        .card-stats-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 8px;
            margin-bottom: 10px;
        }

        .card-odds {
            background: linear-gradient(90deg, #00FF88 0%, #00D2FF 100%);
            color: #0B0E14;
            font-weight: 900;
            font-size: 1.25rem;
            padding: 4px 12px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
        }

        .card-edge {
            color: #00FF88;
            font-weight: 800;
            font-size: 0.95rem;
            font-family: 'Monaco', monospace;
        }

        /* Progress Bar */
        .confidence-bg {
            background: rgba(30, 41, 59, 0.9);
            border-radius: 6px;
            height: 6px;
            width: 100%;
            overflow: hidden;
        }

        .confidence-fill {
            background: linear-gradient(90deg, #00FF88, #00D2FF);
            height: 100%;
            border-radius: 6px;
        }

        /* Metrics Styling */
        [data-testid="stMetric"] {
            background: rgba(18, 24, 36, 0.88) !important;
            border: 1px solid rgba(0, 255, 136, 0.25) !important;
            border-radius: 12px !important;
            padding: 14px !important;
        }

        [data-testid="stMetricValue"] {
            color: #00FF88 !important;
            font-weight: 800 !important;
        }
    </style>
""")

# -----------------------------------------------------------------------------
# 2. COMPLETE PLAYER & TEAM IMAGE MAPPING DATABASE
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
    """Ensures every pick gets a player image or fallback team crest."""
    for player, url in PLAYER_IMAGE_DATABASE.items():
        if player in selection:
            return url
            
    parts = match_str.split(" vs ")
    if len(parts) > 0:
        return CREST_DATABASE.get(parts[0].strip().upper(), "https://upload.wikimedia.org/wikipedia/en/thumb/e/e4/Australian_Football_League.svg/200px-Australian_Football_League.svg.png")
    return "https://upload.wikimedia.org/wikipedia/en/thumb/e/e4/Australian_Football_League.svg/200px-Australian_Football_League.svg.png"

# -----------------------------------------------------------------------------
# 3. SCORING PIPELINE
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
# 4. APP DASHBOARD RENDER
# -----------------------------------------------------------------------------
st.title("⚡ LUCASBETS // CYBER SPORTS CARDS")
st.caption("AFL Sportsbet Value Matrix • Auto-Ranked Confidence Index")

df_raw = load_odds_data()
df_ranked = rank_sportsbet_markets(df_raw, min_odds=1.20)

# Sidebar
st.sidebar.header("🕹️ FILTER CARDS")
selected_match = st.sidebar.selectbox("Match Filter", ["All Round Matches"] + list(df_ranked["match"].unique()))
min_odds_val, max_odds_val = st.sidebar.slider("Odds Band ($)", 1.20, 3.00, (1.20, 2.00), 0.05)
selected_markets = st.sidebar.multiselect("Market Type", list(df_ranked["market_type"].unique()), list(df_ranked["market_type"].unique()))
min_conf_score = st.sidebar.slider("Min Confidence (%)", 50.0, 95.0, 65.0, 1.0)

# Filter Dataset
df_filtered = df_ranked[
    (df_ranked["odds"] >= min_odds_val) &
    (df_ranked["odds"] <= max_odds_val) &
    (df_ranked["market_type"].isin(selected_markets)) &
    (df_ranked["confidence_score"] >= min_conf_score)
].copy()

if selected_match != "All Round Matches":
    df_filtered = df_filtered[df_filtered["match"] == selected_match]

df_filtered["rank"] = range(1, len(df_filtered) + 1)

# Summary Status Bar
m1, m2, m3, m4 = st.columns(4)
m1.metric("Active Markets", len(df_ranked))
m2.metric("Matching Cards", len(df_filtered))
m3.metric("Top Confidence", f"{df_filtered['confidence_score'].max()}%" if not df_filtered.empty else "N/A")
m4.metric("Average Edge", f"{df_filtered['edge_%'].mean():.2f}%" if not df_filtered.empty else "0.00%")

st.divider()

# Navigation Tabs
tab1, tab2, tab3 = st.tabs(["🎴 Sports Card Grid", "🧩 SGM Multi Builder", "🧬 Model Blueprint"])

with tab1:
    if df_filtered.empty:
        st.info("No betting cards fit the current sidebar parameters.")
    else:
        # Display as a grid of 4 cards per row
        cols_per_row = 4
        rows = [df_filtered.iloc[i:i + cols_per_row] for i in range(0, len(df_filtered), cols_per_row)]

        for row in rows:
            cols = st.columns(cols_per_row)
            for idx, (index, item) in enumerate(row.iterrows()):
                with cols[idx]:
                    rank_class = "rank-1-card" if item['rank'] == 1 else ""
                    
                    st.markdown(f"""
                        <div class="sports-card {rank_class}">
                            <div class="card-img-wrapper">
                                <span class="card-rank-badge">#{item['rank']}</span>
                                <span class="card-match-badge">{item['match']}</span>
                                <img src="{item['bet_image']}" alt="{item['selection']}">
                            </div>
                            
                            <div class="card-title">{item['selection']}</div>
                            
                            <div class="card-stats-row">
                                <span class="card-odds">${item['odds']:.2f}</span>
                                <span class="card-edge">+{item['edge_%']:.1f}% Edge</span>
                            </div>
                            
                            <div style="display:flex; justify-content:space-between; font-size:0.75rem; color:#94A3B8; margin-bottom:4px;">
                                <span>CONFIDENCE</span>
                                <span><b style="color:#00FF88;">{item['confidence_score']}%</b></span>
                            </div>
                            <div class="confidence-bg">
                                <div class="confidence-fill" style="width: {item['confidence_score']}%;"></div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

with tab2:
    st.subheader("Cyber Multi Builder")
    col_s1, col_s2 = st.columns([1, 2])
    with col_s1:
        sgm_match = st.selectbox("Target Match", [m for m in list(df_ranked["match"].unique())])
        num_legs = st.slider("Leg Count", 2, 4, 2)
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
                st.markdown(
                    f"<div style='background:rgba(18,24,36,0.8); border:1px solid rgba(0,255,136,0.3); border-radius:10px; padding:12px; margin-bottom:8px;'>"
                    f"<b>Leg {selected_legs.index.get_loc(idx) + 1}:</b> {leg['selection']} | Odds: <b>${leg['odds']:.2f}</b> | Confidence: <b>{leg['confidence_score']}%</b>"
                    f"</div>", 
                    unsafe_allow_html=True
                )

with tab3:
    st.markdown("""
    ### Lucasbets Model Architecture
    * **Model Probability (50%):** Weighted projection from Squiggle API data.
    * **Historical Hit Rate (35%):** Last 10 matches cover rate.
    * **Matchup Matrix (15%):** Defensive concession indexes per stat.
    """)
