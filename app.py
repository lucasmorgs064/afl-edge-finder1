import streamlit as st
import pandas as pd
import json
import os
from ranker import rank_sportsbet_markets

# Set page configuration
st.set_page_config(
    page_title="AFL Analytics - Sportsbet Value Engine",
    page_icon="🏉",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# Data Loading & Caching Function
# -----------------------------------------------------------------------------
@st.cache_data(ttl=900)  # Refresh cache every 15 minutes
def load_odds_data(file_path="data/latest_odds.json"):
    """
    Loads raw odds data from local storage or returns fallback demo data.
    """
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            return pd.DataFrame(data)
        except Exception as e:
            st.error(f"Error reading {file_path}: {e}")
            return pd.DataFrame()
    else:
        # Fallback Mock Data if JSON is missing or during initial testing
        mock_data = [
            {"match": "Fremantle vs WBD", "market_type": "Player Disposals", "selection": "Caleb Serong 25+ Disposals", "odds": 1.28, "projected_prob": 0.84, "hit_rate_l10": 0.90, "matchup_factor": 1.1},
            {"match": "Fremantle vs WBD", "market_type": "Total Goals", "selection": "Josh Treacy 2+ Goals", "odds": 1.38, "projected_prob": 0.78, "hit_rate_l10": 0.80, "matchup_factor": 1.15},
            {"match": "Fremantle vs WBD", "market_type": "Line / Margin", "selection": "Fremantle -18.5 Line", "odds": 1.35, "projected_prob": 0.76, "hit_rate_l10": 0.70, "matchup_factor": 1.05},
            {"match": "Fremantle vs WBD", "market_type": "Player Disposals", "selection": "Andrew Brayshaw 25+ Disposals", "odds": 1.40, "projected_prob": 0.75, "hit_rate_l10": 0.80, "matchup_factor": 1.0},
            {"match": "Fremantle vs WBD", "market_type": "Player Disposals", "selection": "Marcus Bontempelli 25+ Disposals", "odds": 1.52, "projected_prob": 0.71, "hit_rate_l10": 0.70, "matchup_factor": 1.05},
            {"match": "Fremantle vs WBD", "market_type": "Head to Head", "selection": "Fremantle Win", "odds": 1.45, "projected_prob": 0.72, "hit_rate_l10": 0.75, "matchup_factor": 1.0},
            {"match": "MEL vs FRE", "market_type": "Player Disposals", "selection": "Clayton Oliver 25+ Disposals", "odds": 1.32, "projected_prob": 0.81, "hit_rate_l10": 0.85, "matchup_factor": 1.0},
            {"match": "MEL vs FRE", "market_type": "Total Goals", "selection": "Bayley Fritsch 2+ Goals", "odds": 1.62, "projected_prob": 0.65, "hit_rate_l10": 0.60, "matchup_factor": 1.1},
        ]
        return pd.DataFrame(mock_data)

# -----------------------------------------------------------------------------
# Main Application Layout
# -----------------------------------------------------------------------------
st.title("🏉 AFL Sportsbet Value & Confidence Tracker")
st.markdown("Automated confidence ranking and value calculation for all AFL market selections $\\ge \\$1.20$.")

# Load raw dataset
df_raw = load_odds_data()

if df_raw.empty:
    st.warning("No betting data currently available. Check GitHub Actions pipeline status.")
    st.stop()

# Run through confidence ranking engine
df_ranked = rank_sportsbet_markets(df_raw, min_odds=1.20)

# -----------------------------------------------------------------------------
# Sidebar Controls & Filters
# -----------------------------------------------------------------------------
st.sidebar.header("🎯 Analytics Controls")

# Match Selector
available_matches = ["All Matches"] + list(df_ranked["match"].unique())
selected_match = st.sidebar.selectbox("Select Match", available_matches)

# Odds Range Slider
min_odds_val, max_odds_val = st.sidebar.slider(
    "Filter Odds Range",
    min_value=1.20,
    max_value=3.00,
    value=(1.20, 2.00),
    step=0.05
)

# Market Types Multiselect
all_market_types = list(df_ranked["market_type"].unique())
selected_markets = st.sidebar.multiselect(
    "Filter Market Types",
    options=all_market_types,
    default=all_market_types
)

# Minimum Confidence Score Threshold
min_conf_score = st.sidebar.slider(
    "Min Confidence Score (%)",
    min_value=50.0,
    max_value=95.0,
    value=65.0,
    step=1.0
)

# Apply Sidebar Filters
df_filtered = df_ranked[
    (df_ranked["odds"] >= min_odds_val) &
    (df_ranked["odds"] <= max_odds_val) &
    (df_ranked["market_type"].isin(selected_markets)) &
    (df_ranked["confidence_score"] >= min_conf_score)
]

if selected_match != "All Matches":
    df_filtered = df_filtered[df_filtered["match"] == selected_match]

# Re-index Rank Column for Display
df_filtered = df_filtered.copy()
df_filtered["rank"] = range(1, len(df_filtered) + 1)

# -----------------------------------------------------------------------------
# Summary Metrics Header
# -----------------------------------------------------------------------------
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Markets Analyzed", len(df_ranked))
m2.metric("Qualifying Markets", len(df_filtered))

if not df_filtered.empty:
    top_bet = df_filtered.iloc[0]
    m3.metric("Highest Rank Confidence", f"{top_bet['confidence_score']}%", f"{top_bet['selection']}")
    m4.metric("Avg Value Edge", f"{df_filtered['edge_%'].mean():.2f}%")

st.divider()

# -----------------------------------------------------------------------------
# Main Content Tabs
# -----------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["🏆 Ranked Confidence Board", "🧩 Same Game Multi Generator", "ℹ️ Model Methodology"])

with tab1:
    st.subheader("Current Round Market Rankings (Odds $\\ge \\$1.20$)")
    st.caption("Ranked by composite score: Model Probability (50%) + Historical Consistency (35%) + Matchup Rating (15%).")

    if df_filtered.empty:
        st.info("No markets match the currently selected filter criteria.")
    else:
        # Display Styled Data Table
        st.dataframe(
            df_filtered[['rank', 'match', 'market_type', 'selection', 'odds', 'confidence_score', 'edge_%']],
            column_config={
                "rank": st.column_config.NumberColumn("Rank", format="#%d"),
                "match": "Match",
                "market_type": "Category",
                "selection": "Selection / Bet Name",
                "odds": st.column_config.NumberColumn("Odds", format="$%.2f"),
                "confidence_score": st.column_config.ProgressColumn(
                    "Confidence Score",
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
    st.subheader("Automated Same Game Multi (SGM) Builder")
    st.write("Combines top-ranked, high-confidence anchors into a custom multi target.")

    col_sgm1, col_sgm2 = st.columns([1, 2])

    with col_sgm1:
        sgm_match = st.selectbox("Select Match for Multi", [m for m in available_matches if m != "All Matches"])
        target_multi_odds = st.number_input("Target Total Odds ($)", min_value=1.50, max_value=10.00, value=2.00, step=0.10)
        num_legs = st.slider("Target Number of Legs", min_value=2, max_value=4, value=2)

    with col_sgm2:
        # Generate SGM Legs
        sgm_pool = df_ranked[(df_ranked["match"] == sgm_match) & (df_ranked["confidence_score"] >= 70.0)]

        if len(sgm_pool) < num_legs:
            st.warning(f"Not enough high-confidence legs available for {sgm_match} to build a {num_legs}-leg SGM.")
        else:
            selected_legs = sgm_pool.head(num_legs)
            
            # Estimate total odds (compounded with slight reduction for correlation)
            raw_multi_odds = 1.0
            for o in selected_legs["odds"]:
                raw_multi_odds *= o
            
            est_multi_odds = round(raw_multi_odds * 0.92, 2)  # Adjust for standard bookmaker multi margin

            st.markdown(f"### Proposed Multi — Approx. Total Odds: **${est_multi_odds:.2f}**")
            
            for idx, leg in selected_legs.iterrows():
                st.info(f"**Leg {selected_legs.index.get_loc(idx) + 1}:** {leg['selection']} | Odds: **${leg['odds']:.2f}** (Confidence: **{leg['confidence_score']}%**)")

with tab3:
    st.markdown("""
    ### How the Model Ranks Confidence
    
    Rather than relying solely on raw odds, the system evaluates three distinct metrics for every market selection:
    
    1. **Model Projected Probability ($50\%$ Weight):** Implied probability generated by historical team rating systems, Squiggle match projections, and player stat expectancy.
    2. **Historical Cover Rate ($35\%$ Weight):** The percentage of times the selection successfully hit over its last 10 games.
    3. **Matchup Rating ($15\%$ Weight):** Adjusts for opposition tendencies (e.g., how heavily the opposition concedes disposals or forward goals).
    
    All selections are re-calculated daily via GitHub Actions workflows and updated in real-time.
    """)

st.sidebar.caption("Data updated daily via GitHub Actions.")
