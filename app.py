import os
import requests
import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(page_title="AFL +EV Bet Finder", page_icon="🏉", layout="wide")

# -------------------------------------------------------------------
# Configuration & API Key
# -------------------------------------------------------------------
API_KEY = st.secrets.get("ODDS_API_KEY", os.environ.get("ODDS_API_KEY", "f9366aa6d54b45008ab1df1b44634266"))
SPORT = "aussierules_afl"
REGIONS = "au"
MARKETS = "h2h"

# Required by Squiggle API Guidelines
SQUIGGLE_HEADERS = {"User-Agent": "AFL Analytics App - student@college.edu"}

# -------------------------------------------------------------------
# Fetch Model Predictions from Squiggle
# -------------------------------------------------------------------
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_squiggle_tips(year=2026):
    """Fetches computer model match tips/probabilities from Squiggle."""
    url = f"https://api.squiggle.com.au/?q=tips;year={year}"
    try:
        response = requests.get(url, headers=SQUIGGLE_HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json().get("tips", [])
        return pd.DataFrame(data), None
    except Exception as e:
        return pd.DataFrame(), str(e)

# -------------------------------------------------------------------
# Fetch Live SportsBet Odds
# -------------------------------------------------------------------
@st.cache_data(ttl=600, show_spinner=False)
def fetch_afl_odds(api_key: str):
    """Fetches upcoming AFL odds from The Odds API."""
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
# Match Odds with Model & Calculate EV
# -------------------------------------------------------------------
def calculate_value_bets(odds_data, tips_df):
    """Compares bookmaker odds against Squiggle model predictions to find +EV."""
    rows = []
    
    # Process Squiggle model probabilities
    squiggle_probs = {}
    if not tips_df.empty and "hmargin" in tips_df.columns:
        # Get latest predictions per match
        for _, tip in tips_df.iterrows():
            hteam = tip.get("hteam")
            ateam = tip.get("ateam")
            hprob = tip.get("hprop", 0.5)  # Home win probability
            squiggle_probs[hteam] = float(hprob)
            squiggle_probs[ateam] = 1.0 - float(hprob)

    for game in odds_data:
        home_team = game.get("home_team")
        away_team = game.get("away_team")
        commence_time = pd.to_datetime(game.get("commence_time")).tz_convert("Australia/Melbourne")
        
        for bookmaker in game.get("bookmakers", []):
            bm_title = bookmaker.get("title")
            for market in bookmaker.get("markets", []):
                if market.get("key") == "h2h":
                    for outcome in market.get("outcomes", []):
                        team_name = outcome.get("name")
                        odds = outcome.get("price", 1.0)
                        
                        # Match team to Squiggle probability (fuzzy fallback to 50% if unmapped)
                        model_prob = squiggle_probs.get(team_name, 0.50)
                        
                        # Calculate Expected Value
                        ev = (model_prob * odds) - 1.0
                        
                        rows.append({
                            "Matchup": f"{home_team} vs {away_team}",
                            "Kickoff": commence_time.strftime("%a %d %b, %I:%M %p"),
                            "Bookmaker": bm_title,
                            "Team": team_name,
                            "Odds": odds,
                            "Model Probability": f"{round(model_prob * 100, 1)}%",
                            "Expected Value (EV)": f"{'+' if ev > 0 else ''}{round(ev * 100, 1)}%",
                            "EV_raw": ev,
                            "Recommendation": "✅ RECOMMENDED VALUE BET" if ev > 0 else "❌ No Value"
                        })
    
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(by="EV_raw", ascending=False).drop(columns=["EV_raw"])
    return df

# -------------------------------------------------------------------
# Dashboard UI
# -------------------------------------------------------------------
st.title("🏉 AFL Smart Bet Finder (+EV Recommendations)")

# Sidebar Controls
st.sidebar.header("Controls")
if st.sidebar.button("🔄 Refresh Data & Odds"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
only_recommended = st.sidebar.checkbox("Show Only Recommended Bets (+EV)", value=False)

# Fetch Data
with st.spinner("Analyzing model predictions and live odds..."):
    odds_raw, odds_err = fetch_afl_odds(API_KEY)
    tips_df, tips_err = fetch_squiggle_tips(year=2026)

if odds_err:
    st.error(f"Error fetching odds: {odds_err}")
    st.stop()

if not odds_raw:
    st.warning("No live odds returned.")
    st.stop()

# Generate Value Bet Table
value_df = calculate_value_bets(odds_raw, tips_df)

if only_recommended and not value_df.empty:
    value_df = value_df[value_df["Recommendation"].str.contains("RECOMMENDED")]

st.subheader("Match Predictions & Odds Analysis")
st.dataframe(value_df, use_container_width=True)
