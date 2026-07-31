import os
import requests
import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(page_title="AFL Multi-Market +EV Bet Finder", page_icon="🏉", layout="wide")

# -------------------------------------------------------------------
# Configuration & API Key Setup
# -------------------------------------------------------------------
API_KEY = st.secrets.get("ODDS_API_KEY", os.environ.get("ODDS_API_KEY", "f9366aa6d54b45008ab1df1b44634266"))
SPORT = "aussierules_afl"
REGIONS = "au"
MARKETS = "h2h,spreads,totals"  # Pull Head-to-Head, Line Spreads, and Over/Under Totals

SQUIGGLE_HEADERS = {"User-Agent": "AFL Analytics Dashboard - student@college.edu"}

# -------------------------------------------------------------------
# Data Fetching Functions
# -------------------------------------------------------------------
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_squiggle_tips(year=2026):
    """Fetches computer model predictions from Squiggle."""
    url = f"https://api.squiggle.com.au/?q=tips;year={year}"
    try:
        response = requests.get(url, headers=SQUIGGLE_HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json().get("tips", [])
        return pd.DataFrame(data), None
    except Exception as e:
        return pd.DataFrame(), str(e)

@st.cache_data(ttl=600, show_spinner=False)
def fetch_afl_odds(api_key: str):
    """Fetches live AFL odds across all primary Australian markets."""
    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds/"
    params = {
        "apiKey": api_key,
        "regions": REGIONS,
        "markets": MARKETS,
        "dateFormat": "iso",
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.RequestException as e:
        return None, str(e)

# -------------------------------------------------------------------
# Multi-Market Data Processing & EV Calculation
# -------------------------------------------------------------------
def process_multi_market_odds(odds_data, tips_df):
    """Processes H2H, Spread, and Totals markets and calculates expected values."""
    rows = []
    
    # Extract Squiggle model probabilities
    squiggle_probs = {}
    if not tips_df.empty and "hprop" in tips_df.columns:
        for _, tip in tips_df.iterrows():
            hteam = tip.get("hteam")
            ateam = tip.get("ateam")
            hprob = float(tip.get("hprop", 0.5))
            squiggle_probs[hteam] = hprob
            squiggle_probs[ateam] = 1.0 - hprob

    for game in odds_data:
        home_team = game.get("home_team")
        away_team = game.get("away_team")
        commence_dt = pd.to_datetime(game.get("commence_time")).tz_convert("Australia/Melbourne")
        kickoff_str = commence_dt.strftime("%a %d %b, %I:%M %p")
        
        for bookmaker in game.get("bookmakers", []):
            bm_title = bookmaker.get("title")
            for market in bookmaker.get("markets", []):
                mkt_key = market.get("key")
                
                # Market Labeling
                mkt_name = "Head to Head"
                if mkt_key == "spreads":
                    mkt_name = "Line / Spread"
                elif mkt_key == "totals":
                    mkt_name = "Total Points"

                for outcome in market.get("outcomes", []):
                    team_or_type = outcome.get("name")
                    price = outcome.get("price", 1.0)
                    point = outcome.get("point", None)
                    
                    # Target selection description
                    target_desc = team_or_type
                    if point is not None:
                        target_desc = f"{team_or_type} ({'+' if point > 0 else ''}{point})"
                    
                    # Model probability mapping (Baseline 50% for standard lines/totals)
                    model_prob = squiggle_probs.get(team_or_type, 0.50)
                    if mkt_key in ["spreads", "totals"]:
                        model_prob = 0.525  # Estimated baseline model edge threshold for spreads/totals
                    
                    # Expected Value calculation
                    ev = (model_prob * price) - 1.0
                    
                    rows.append({
                        "commence_dt": commence_dt,
                        "Kickoff": kickoff_str,
                        "Matchup": f"{home_team} vs {away_team}",
                        "Bookmaker": bm_title,
                        "Market": mkt_name,
                        "Selection": target_desc,
                        "Odds": price,
                        "Model Win Prob": f"{round(model_prob * 100, 1)}%",
                        "Expected Value (EV)": f"{'+' if ev > 0 else ''}{round(ev * 100, 1)}%",
                        "EV_raw": ev,
                        "Recommendation": "✅ RECOMMENDED VALUE BET" if ev > 0 else "❌ No Value"
                    })
    
    df = pd.DataFrame(rows)
    if not df.empty:
        # Sort chronologically by game kickoff time first, then highest EV
        df = df.sort_values(by=["commence_dt", "EV_raw"], ascending=[True, False])
        df = df.drop(columns=["commence_dt", "EV_raw"])
    return df

# -------------------------------------------------------------------
# User Interface & Dashboard Logic
# -------------------------------------------------------------------
st.title("🏉 AFL Smart Betting Dashboard")
st.caption("Live odds, chronological match schedules, multi-bookmaker filters, and +EV recommendations.")

# Sidebar Filters
st.sidebar.header("Filter & Controls")

if st.sidebar.button("🔄 Force Refresh Data"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")

# Load Raw Data
with st.spinner("Fetching latest live odds and model tips..."):
    odds_raw, odds_err = fetch_afl_odds(API_KEY)
    tips_df, tips_err = fetch_squiggle_tips(year=2026)

if odds_err:
    st.error(f"Error connecting to odds API: {odds_err}")
    st.stop()

if not odds_raw:
    st.warning("No odds data currently returned.")
    st.stop()

# Build DataFrame
df = process_multi_market_odds(odds_raw, tips_df)

if not df.empty:
    # 1. Bookmaker Multi-Select Filter
    available_bookies = sorted(list(df["Bookmaker"].unique()))
    selected_bookies = st.sidebar.multiselect(
        "Select Betting Apps / Bookmakers:",
        options=available_bookies,
        default=available_bookies
    )
    
    # 2. Market Filter
    available_markets = list(df["Market"].unique())
    selected_markets = st.sidebar.multiselect(
        "Select Betting Markets:",
        options=available_markets,
        default=available_markets
    )
    
    # 3. Recommendation Toggle
    only_value = st.sidebar.checkbox("Show Only Recommended Value Bets (+EV)", value=False)
    
    # Apply Filters
    filtered_df = df[
        (df["Bookmaker"].isin(selected_bookies)) & 
        (df["Market"].isin(selected_markets))
    ]
    
    if only_value:
        filtered_df = filtered_df[filtered_df["Recommendation"].str.contains("RECOMMENDED")]
    
    st.subheader(f"Upcoming Matches & Market Odds ({len(filtered_df)} bets listed)")
    st.dataframe(filtered_df, use_container_width=True)
else:
    st.info("No odds available to display.")
