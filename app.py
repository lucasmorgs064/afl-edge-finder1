import streamlit as st
import pandas as pd
import numpy as np
import json
import os

# Set page configuration with dark theme default
st.set_page_config(
    page_title="AFL CyberEdge // Value Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 1. Futuristic Cyberpunk CSS Theme Injection
# -----------------------------------------------------------------------------
st.html("""
    <style>
        .stApp {
            background-color: #0B0E14;
            color: #E2E8F0;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        
        h1, h2, h3 {
            color: #00FF88 !important;
            font-weight: 800 !important;
            letter-spacing: -0.5px;
            text-transform: uppercase;
        }

        .hero-card {
            background: linear-gradient(135deg, rgba(0, 255, 136, 0.1) 0%, rgba(14, 23, 38, 0.9) 100%);
            border: 1px solid #00FF88;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 0 25px rgba(0, 255, 136, 0.15);
            margin-bottom: 25px;
        }

        .hero-badge {
            background: #00FF88;
            color: #0B0E14;
            font-weight: 900;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            text-transform: uppercase;
        }

        [data-testid="stMetric"] {
            background: #121824;
            border: 1px solid #1E293B;
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            transition: transform 0.2s ease, border-color 0.2s ease;
        }
        
        [data-testid="stMetric"]:hover {
            border-color: #00FF88;
            transform: translateY(-2px);
        }

        [data-testid="stMetricLabel"] {
            color: #94A3B8 !important;
            font-size: 0.85rem !important;
            text-transform: uppercase;
        }

        [data-testid="stMetricValue"] {
            color: #00FF88 !important;
            font-weight: 700 !important;
        }

        .stDataFrame {
            border: 1px solid #1E293B;
            border-radius: 12px;
            overflow: hidden;
            background: #121824;
        }

        .sgm-leg-card {
            background: #121824;
            border-left: 4px solid #00FF88;
            padding: 14px 18px;
            border-radius: 8px;
            margin-bottom: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }
    </style>
""")

# -----------------------------------------------------------------------------
# 2. Team Crest URL Mapping
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

def get_match_crest_url(match_string):
    """Extracts home team code from 'HOME vs AWAY' and returns crest logo URL."""
    parts = match_string.split(" vs ")
    if len(parts) > 0:
        team_code = parts[0].strip().upper()
        return CREST_DATABASE.get(team_code, "https://upload.wikimedia.org/wikipedia/en/thumb/e/e4/Australian_Football_League.svg/200px-Australian_Football_League.svg.png")
    return "https://upload.wikimedia.org/wikipedia/en/thumb/e/e4/Australian_Football_League.svg/200px-Australian_Football_League.svg.png"

# -----------------------------------------------------------------------------
# 3. Ranking & Scoring Logic
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
    df['crest_url'] = df['match'].apply(get_match_crest_url)
    df = df.sort_values(by=['confidence_score', 'edge_%'], ascending=[False, False])
    return df

# Hero Image Database Mapping
IMAGE_DATABASE = {
    "Caleb Serong": "https://encrypted-tbn2.gstatic.com/licensed-image?q=tbn:ANd9GcQ_eGg5rGeJ6ybuBG_x1TVPeqlYGBmA_FjhV8QwEvFsq9XFCNYUjFzClJmbBr6aG0i2rcWErmGBISc09UM",
    "Marcus Bontempelli": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Marcus_Bontempelli_2019.1.jpg/800px-Marcus_Bontempelli_2019.1.jpg",
    "Fremantle": "https://upload.wikimedia.org/wikipedia/en/thumb/e/e0/Fremantle_FC_logo.svg/1200px-Fremantle_FC_logo.svg.png",
    "Western Bulldogs": "https://upload.wikimedia.org/wikipedia/en/thumb/8/87/Western_Bulldogs_logo.svg/1200px-Western_Bulldogs_logo.svg.png"
}

def get_image_for_bet(selection, market_type):
    for entity, url in IMAGE_DATABASE.items():
        if entity in selection:
            return url
    return "https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?auto=format&fit=crop&w=800&q=80"

# -----------------------------------------------------------------------------
# 4. Data Loader Function
# -----------------------------------------------------------------------------
@st.cache_data(ttl=300)
def load_odds_data(file_path="data/latest_odds.json"):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            return pd.DataFrame(data)
        except Exception:
            pass
            
    mock_data = [
        {"round": 22, "match": "MEL vs FRE", "market_type": "Player Disposals", "selection": "Caleb Serong 25+ Disposals", "odds": 1.28, "projected_prob": 0.85, "hit_rate_l10": 0.90, "matchup_factor": 1.10},
        {"round": 22, "match": "WBD vs NTH", "market_type": "Player Disposals", "selection": "Marcus Bontempelli 25+ Disposals", "odds": 1.30, "projected_prob": 0.82, "hit_rate_l10": 0.85, "matchup_factor": 1.10},
        {"round": 22, "match": "MEL vs FRE", "market_type": "Total Goals", "selection": "Josh Treacy 2+ Goals", "odds": 1.40, "projected_prob": 0.77, "hit_rate_l10": 0.80, "matchup_factor": 1.15},
        {"round": 22, "match": "MEL vs FRE", "market_type": "Head to Head", "selection": "Fremantle Win", "odds": 1.45, "projected_prob": 0.73, "hit_rate_l10": 0.75, "matchup_factor": 1.00},
        {"round": 22, "match": "BRI vs HAW", "market_type": "Player Disposals", "selection": "Lachie Neale 25+ Disposals", "odds": 1.35, "projected_prob": 0.80, "hit_rate_l10": 0.80, "matchup_factor": 1.05},
        {"round": 22, "match": "SYD vs PTA", "market_type": "Player Disposals", "selection": "Errol Gulden 25+ Disposals", "odds": 1.38, "projected_prob": 0.78, "hit_rate_l10": 0.80, "matchup_factor": 1.00},
    ]
    return pd.DataFrame(mock_data)

# -----------------------------------------------------------------------------
# 5. Main App Rendering
# -----------------------------------------------------------------------------
st.title("⚡ AFL CYBEREDGE // VALUE ENGINE")
st.caption("AI-Powered Confidence Ranking Terminal • Sportsbet AFL Markets $\\ge \\$1.20$")

df_raw = load_odds_data()
df_ranked = rank_sportsbet_markets(df_raw, min_odds=1.20)

# Sidebar Controls
st.sidebar.header("🕹️ TERMINAL CONTROLS")
available_matches = ["All Round Matches"] + list(df_ranked["match"].unique())
selected_match = st.sidebar.selectbox("Match Filter", available_matches)

min_odds_val, max_odds_val = st.sidebar.slider(
    "Odds Range ($)",
    min_value=1.20,
    max_value=3.00,
    value=(1.20, 2.00),
    step=0.05
)

selected_markets = st.sidebar.multiselect(
    "Market Filter",
    options=list(df_ranked["market_type"].unique()),
    default=list(df_ranked["market_type"].unique())
)

min_conf_score = st.sidebar.slider(
    "Min Confidence Threshold (%)",
    min_value=50.0,
    max_value=95.0,
    value=65.0,
    step=1.0
)

# Apply Filters
df_filtered = df_ranked[
    (df_ranked["odds"] >= min_odds_val) &
    (df_ranked["odds"] <= max_odds_val) &
    (df_ranked["market_type"].isin(selected_markets)) &
    (df_ranked["confidence_score"] >= min_conf_score)
].copy()

if selected_match != "All Round Matches":
    df_filtered = df_filtered[df_filtered["match"] == selected_match]

df_filtered["rank"] = range(1, len(df_filtered) + 1)

# --- TOP PICK HERO HIGHLIGHT SECTION ---
if not df_filtered.empty:
    top_bet = df_filtered.iloc[0]
    top_img_url = get_image_for_bet(top_bet['selection'], top_bet['market_type'])
    
    st.markdown('<div class="hero-card">', unsafe_allow_html=True)
    c1, c2 = st.columns([1, 2.5])
    
    with c1:
        st.image(top_img_url, use_container_width=True)
        
    with c2:
        st.markdown('<span class="hero-badge">⚡ #1 HIGHEST CONFIDENCE PICK</span>', unsafe_allow_html=True)
        st.markdown(f"## {top_bet['selection']}")
        st.markdown(f"**Match:** {top_bet['match']} | **Market:** {top_bet['market_type']}")
        
        k1, k2, k3 = st.columns(3)
        k1.metric("Confidence Score", f"{top_bet['confidence_score']}%")
        k2.metric("Sportsbet Odds", f"${top_bet['odds']:.2f}")
        k3.metric("Model Edge", f"{top_bet['edge_%']:+.2f}%")
        
    st.markdown('</div>', unsafe_allow_html=True)

# Metrics Grid
m1, m2, m3 = st.columns(3)
m1.metric("Active Round Markets", len(df_ranked))
m2.metric("Filtered Candidates", len(df_filtered))
m3.metric("Avg Filtered Edge", f"{df_filtered['edge_%'].mean():.2f}%" if not df_filtered.empty else "0.00%")

st.divider()

# Main Display Tabs
tab1, tab2, tab3 = st.tabs(["📊 Live Value Matrix", "🧩 SGM Engine", "🧬 Model Blueprint"])

with tab1:
    st.subheader("Market Rankings Matrix (Odds $\\ge \\$1.20$)")
    if df_filtered.empty:
        st.info("No market selections fit current search parameters.")
    else:
        st.dataframe(
            df_filtered[['rank', 'crest_url', 'match', 'market_type', 'selection', 'odds', 'confidence_score', 'edge_%']],
            column_config={
                "rank": st.column_config.NumberColumn("Rank", format="#%d"),
                "crest_url": st.column_config.ImageColumn("Crest", help="Home Team Crest"),
                "match": "Fixture",
                "market_type": "Category",
                "selection": "Selection Name",
                "odds": st.column_config.NumberColumn("Odds", format="$%.2f"),
                "confidence_score": st.column_config.ProgressColumn(
                    "Confidence Index",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100
                ),
                "edge_%": st.column_config.NumberColumn("Model Edge", format="%+.2f%%"),
            },
            hide_index=True,
            use_container_width=True
        )

with tab2:
    st.subheader("Cyber SGM Multi Generator")
    col_s1, col_s2 = st.columns([1, 2])

    with col_s1:
        sgm_match = st.selectbox("Select Target Match", [m for m in available_matches if m != "All Round Matches"])
        num_legs = st.slider("Number of Legs", min_value=2, max_value=4, value=2)

    with col_s2:
        sgm_pool = df_ranked[(df_ranked["match"] == sgm_match) & (df_ranked["confidence_score"] >= 70.0)]

        if len(sgm_pool) < num_legs:
            st.warning(f"Insufficient high-confidence legs to assemble a {num_legs}-leg SGM for {sgm_match}.")
        else:
            selected_legs = sgm_pool.head(num_legs)
            raw_multi = 1.0
            for o in selected_legs["odds"]:
                raw_multi *= o
            est_multi = round(raw_multi * 0.92, 2)

            st.markdown(f"### Target Multi Odds: **${est_multi:.2f}**")
            for idx, leg in selected_legs.iterrows():
                st.markdown(
                    f'<div class="sgm-leg-card">'
                    f'<b>Leg {selected_legs.index.get_loc(idx) + 1}:</b> {leg["selection"]} | '
                    f'Odds: <b>${leg["odds"]:.2f}</b> | Confidence: <b>{leg["confidence_score"]}%</b>'
                    f'</div>',
                    unsafe_allow_html=True
                )

with tab3:
    st.markdown("""
    ### Confidence Evaluation Engine
    * **Model Projected Probability (50%):** Win/stat probabilities generated via Squiggle match projections and player stat expectancy.
    * **Historical Hit Rate (35%):** Player cover rate over last 10 games.
    * **Matchup Matrix (15%):** Opposition concession ratings for specific stat lines.
    """)
