import streamlit as st
import pandas as pd
import numpy as np
import json
import os

# Page Config
st.set_page_config(
    page_title="LUCASBETS // CYBER SPORTS CARDS",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 1. CYBER HUD CSS WITH DIAGONAL 'LUCASBETS' WATERMARK
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    /* Dark Background + Diagonal LUCASBETS Watermark */
    .stApp {
        background: 
            url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='220' height='220' viewBox='0 0 220 220'><text x='50%' y='50%' fill='rgba(0, 255, 136, 0.04)' font-size='22' font-family='sans-serif' font-weight='900' text-anchor='middle' dominant-baseline='middle' transform='rotate(-35 110 110)'>LUCASBETS</text></svg>"),
            radial-gradient(circle at 50% 20%, rgba(0, 255, 136, 0.08) 0%, rgba(11, 14, 20, 0.97) 75%),
            url("https://images.unsplash.com/photo-1508098682722-e99c43a406b2?auto=format&fit=crop&w=1920&q=80");
        background-size: 220px 220px, cover, cover;
        background-attachment: fixed;
        color: #E2E8F0;
        font-family: 'Inter', -apple-system, sans-serif;
    }

    /* Sports Card Container Styling */
    .card-box {
        background: rgba(18, 24, 36, 0.85);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(0, 255, 136, 0.3);
        border-radius: 14px;
        padding: 14px;
        margin-bottom: 15px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
    }

    /* Rank #1 Highlight Card */
    .card-rank-1 {
        border: 2px solid #00FF88 !important;
        box-shadow: 0 0 20px rgba(0, 255, 136, 0.3) !important;
    }

    /* Smaller Image Box Container */
    .img-box {
        text-align: center;
        background: radial-gradient(circle at center, rgba(0,255,136,0.12) 0%, rgba(15,23,42,0.6) 100%);
        border-radius: 10px;
        padding: 6px;
        margin-bottom: 10px;
        border: 1px solid rgba(0, 255, 136, 0.15);
        height: 85px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .img-box img {
        max-height: 75px;
        max-width: 100%;
        object-fit: contain;
        filter: drop-shadow(0px 4px 6px rgba(0, 0, 0, 0.6));
    }

    /* Card Header Tags */
    .badge-rank {
        background: #00FF88;
        color: #0B0E14;
        font-weight: 900;
        font-size: 0.75rem;
        padding: 2px 8px;
        border-radius: 6px;
        display: inline-block;
    }

    .badge-match {
        color: #94A3B8;
        font-size: 0.75rem;
        font-weight: 700;
        float: right;
        text-transform: uppercase;
    }

    /* Selection Title */
    .selection-text {
        color: #FFFFFF;
        font-weight: 800;
        font-size: 1rem;
        margin-top: 8px;
        margin-bottom: 6px;
        min-height: 2.4rem;
        line-height: 1.2;
    }

    /* Odds & Edge Display */
    .odds-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }

    .odds-val {
        background: linear-gradient(90deg, #00FF88 0%, #00D2FF 100%);
        color: #0B0E14;
        font-weight: 900;
        font-size: 1.1rem;
        padding: 3px 10px;
        border-radius: 8px;
    }

    .edge-val {
        color: #00FF88;
        font-weight: 800;
        font-size: 0.85rem;
    }

    /* Progress Bar */
    .bar-bg {
        background: rgba(30, 41, 59, 0.8);
        border-radius: 5px;
        height: 6px;
        width: 100%;
        overflow: hidden;
        margin-top: 4px;
    }

    .bar-fill {
        background: linear-gradient(90deg, #00FF88, #00D2FF);
        height: 100%;
    }

    /* Custom Metrics */
    [data-testid="stMetric"] {
        background: rgba(18, 24, 36, 0.85) !important;
        border: 1px solid rgba(0, 255, 136, 0.25) !important;
        border-radius: 12px !important;
        padding: 12px !important;
    }

    [data-testid="stMetricValue"] {
        color: #00FF88 !important;
        font-weight: 800 !important;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. ACCURATE PLAYER & CLUB CREST DATABASE
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
    "Caleb Serong": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/eb/Caleb_Serong_2022.1.jpg/440px-Caleb_Serong_2022.1.jpg",
    "Marcus Bontempelli": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Marcus_Bontempelli_2019.1.jpg/440px-Marcus_Bontempelli_2019.1.jpg",
    "Lachie Neale": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d6/Lachie_Neale_2019.1.jpg/440px-Lachie_Neale_2019.1.jpg",
    "Errol Gulden": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c8/Errol_Gulden_2023.1.jpg/440px-Errol_Gulden_2023.1.jpg",
    "Josh Treacy": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/Josh_Treacy_2022.1.jpg/440px-Josh_Treacy_2022.1.jpg",
    "Joe Daniher": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3b/Joe_Daniher_2019.1.jpg/440px-Joe_Daniher_2019.1.jpg"
}

def get_bet_image(selection, match_str):
    # Match player name directly
    for player, url in PLAYER_IMAGE_DATABASE.items():
        if player.lower() in selection.lower():
            return url
            
    # Fallback to team crest logo if H2H or general market
    parts = match_str.split(" vs ")
    if len(parts) > 0:
        team_code = parts[0].strip().upper()
        if team_code in CREST_DATABASE:
            return CREST_DATABASE[team_code]
            
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
# 4. DASHBOARD RENDER
# -----------------------------------------------------------------------------
st.title("⚡ LUCASBETS // CYBER SPORTS CARDS")
st.caption("AFL Sportsbet Value Matrix • Auto-Ranked Confidence Index")

df_raw = load_odds_data()
df_ranked = rank_sportsbet_markets(df_raw, min_odds=1.20)

# Sidebar
st.sidebar.header("🕹️ FILTER TERMINAL")
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

# Summary Top Row Metrics
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
        # Render cards in a 4-column grid
        cols_per_row = 4
        rows = [df_filtered.iloc[i:i + cols_per_row] for i in range(0, len(df_filtered), cols_per_row)]

        for row in rows:
            cols = st.columns(cols_per_row)
            for idx, (_, item) in enumerate(row.iterrows()):
                with cols[idx]:
                    rank_class = "card-rank-1" if item['rank'] == 1 else ""
                    
                    card_html = f"""<div class="card-box {rank_class}">
<div>
<span class="badge-rank">#{item['rank']}</span>
<span class="badge-match">{item['match']}</span>
</div>
<div class="img-box">
<img src="{item['bet_image']}" alt="{item['selection']}">
</div>
<div class="selection-text">{item['selection']}</div>
<div class="odds-row">
<span class="odds-val">${item['odds']:.2f}</span>
<span class="edge-val">+{item['edge_%']:.1f}% Edge</span>
</div>
<div style="display:flex; justify-content:space-between; font-size:0.75rem; color:#94A3B8;">
<span>Confidence</span>
<span style="color:#00FF88; font-weight:bold;">{item['confidence_score']}%</span>
</div>
<div class="bar-bg">
<div class="bar-fill" style="width: {item['confidence_score']}%;"></div>
</div>
</div>"""
                    st.markdown(card_html, unsafe_allow_html=True)

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
