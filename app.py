import os
import requests
import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(page_title="AFL Odds & Analytics", page_icon="🏉", layout="wide")

# -------------------------------------------------------------------
# Configuration & API Key Setup
# -------------------------------------------------------------------
# Attempts to get API key from Streamlit Secrets or Environment Variables
API_KEY = st.secrets.get("ODDS_API_KEY", os.environ.get("ODDS_API_KEY", "YOUR_API_KEY_HERE"))
SPORT = "aussierules_afl"
REGIONS = "au"           # Australian bookmakers (Sportsbet, TAB, Ladbrokes, etc.)
MARKETS = "h2h,spreads"   # Head-to-head and line betting

# -------------------------------------------------------------------
# Data Fetching with 10-Minute Cache Expiration (ttl=600)
# -------------------------------------------------------------------
@st.cache_data(ttl=600, show_spinner=False)
def fetch_afl_odds(api_key: str):
    """
    Fetches upcoming and live AFL odds from The Odds API.
    Cached for 600 seconds (10 minutes) to stay current without exceeding rate limits.
    """
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
# Data Transformation Helper
# -------------------------------------------------------------------
def process_odds_payload(data):
    """Parses raw JSON from The Odds API into a clean DataFrame."""
    games = []
    for game in data:
        home_team = game.get("home_team")
        away_team = game.get("away_team")
        commence_time = pd.to_datetime(game.get("commence_time")).tz_convert("Australia/Melbourne")
        
        for bookmaker in game.get("bookmakers", []):
            bm_title = bookmaker.get("title")
            for market in bookmaker.get("markets", []):
                mkt_key = market.get("key")
                for outcome in market.get("outcomes", []):
                    games.append({
                        "Matchup": f"{home_team} vs {away_team}",
                        "Kickoff": commence_time.strftime("%a %d %b, %I:%M %p"),
                        "Bookmaker": bm_title,
                        "Market": "Head to Head" if mkt_key == "h2h" else "Line/Spread",
                        "Team": outcome.get("name"),
                        "Price": outcome.get("price"),
                        "Point": outcome.get("point", "-")
                    })
    return pd.DataFrame(games)

# -------------------------------------------------------------------
# Main App UI & Sidebar
# -------------------------------------------------------------------
st.title("🏉 AFL Live Odds & Analytics Dashboard")

# Sidebar Controls
st.sidebar.header("Controls & Refresh")

# Manual Cache Clear & Force Reload Button
if st.sidebar.button("🔄 Force Refresh Data"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.info("Data auto-refreshes every 10 minutes.")

# Check API Key
if API_KEY == "YOUR_API_KEY_HERE" or not API_KEY:
    st.error("Missing API Key! Please set `ODDS_API_KEY` in your Streamlit Secrets or code.")
    st.stop()

# Fetch Data
with st.spinner("Fetching latest AFL odds..."):
    raw_data, error = fetch_afl_odds(API_KEY)

if error:
    st.error(f"Failed to retrieve data from API: {error}")
    st.stop()

if not raw_data:
    st.warning("No upcoming AFL games found or API quota reached.")
    st.stop()

# Process & Display Data
df = process_odds_payload(raw_data)

if not df.empty:
    st.subheader("Upcoming Fixtures & Odds")
    
    # Simple Filters
    bookmakers = st.multiselect("Filter by Bookmaker", options=df["Bookmaker"].unique(), default=df["Bookmaker"].unique())
    filtered_df = df[df["Bookmaker"].isin(bookmakers)]
    
    st.dataframe(filtered_df, use_container_width=True)
else:
    st.info("No odds available for display.")
