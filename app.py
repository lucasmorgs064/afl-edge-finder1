import os
import requests
import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(page_title="AFL Sportsbet +EV Dashboard", page_icon="🏉", layout="wide")

# -------------------------------------------------------------------
# Configuration & API Setup
# -------------------------------------------------------------------
API_KEY = st.secrets.get("ODDS_API_KEY", os.environ.get("ODDS_API_KEY", "f9366aa6d54b45008ab1df1b44634266"))
SPORT = "aussierules_afl"
REGIONS = "au"
MARKETS = "h2h,spreads,totals"
TARGET_BOOKMAKER = "sportsbet"

SQUIGGLE_HEADERS = {"User-Agent": "AFL Analytics Dashboard - student@college.edu"}

# Canonical AFL Team Names Mapping
TEAM_MAP = {
    "Adelaide Crows": "Adelaide", "Adelaide": "Adelaide",
    "Brisbane Lions": "Brisbane", "Brisbane": "Brisbane",
    "Carlton Blues": "Carlton", "Carlton": "Carlton",
    "Collingwood Magpies": "Collingwood", "Collingwood": "Collingwood",
    "Essendon Bombers": "Essendon", "Essendon": "Essendon",
    "Fremantle Dockers": "Fremantle", "Fremantle": "Fremantle",
    "Geelong Cats": "Geelong", "Geelong": "Geelong",
    "Gold Coast Suns": "Gold Coast", "Gold Coast": "Gold Coast",
    "Greater Western Sydney Giants": "GWS", "GWS Giants": "GWS", "GWS": "GWS",
    "Hawthorn Hawks": "Hawthorn", "Hawthorn": "Hawthorn",
    "Melbourne Demons": "Melbourne", "Melbourne": "Melbourne",
    "North Melbourne Kangaroos": "North Melbourne", "North Melbourne": "North Melbourne",
    "Port Adelaide Power": "Port Adelaide", "Port Adelaide": "Port Adelaide",
    "Richmond Tigers": "Richmond", "Richmond": "Richmond",
    "St Kilda Saints": "St Kilda", "St Kilda": "St Kilda",
    "Sydney Swans": "Sydney", "Sydney": "Sydney",
    "West Coast Eagles": "West Coast", "West Coast": "West Coast",
    "Western Bulldogs": "Western Bulldogs", "Bulldogs": "Western Bulldogs"
}

def clean_team_name(name):
    """Normalizes team names to match Squiggle API conventions."""
    if not name:
        return name
    return TEAM_MAP.get(str(name).strip(), str(name).strip())

# -------------------------------------------------------------------
# Data Fetching
# -------------------------------------------------------------------
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_squiggle_tips(year=2026):
    url = f"https://api.squiggle.com.au/?q=tips;year={year}"
    try:
        response = requests.get(url, headers=SQUIGGLE_HEADERS, timeout=10)
        response.raise_for_status()
        return pd.DataFrame(response.json().get("tips", [])), None
    except Exception as e:
        return pd.DataFrame(), str(e)

@st.cache_data(ttl=600, show_spinner=False)
def fetch_sportsbet_odds(api_key: str):
    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds/"
    params = {
        "apiKey": api_key,
        "regions": REGIONS,
        "markets": MARKETS,
        "bookmakers": TARGET_BOOKMAKER,
        "dateFormat": "iso",
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.RequestException as e:
        return None, str(e)

# -------------------------------------------------------------------
# Matchup Probability Builder
# -------------------------------------------------------------------
def build_matchup_probabilities(tips_df):
    """
    Groups Squiggle tips by upcoming Matchup (Home vs Away) 
    and averages hprop across all prediction models.
    """
    matchup_probs = {}
    if tips_df.empty or "hprop" not in tips_df.columns:
        return matchup_probs

    # Filter for valid numeric hprop values
    tips_df["hprop_num"] = pd.to_numeric(tips_df["hprop"], errors="coerce")
    valid_tips = tips_df.dropna(subset=["hprop_num"])

    for _, row in valid_tips.iterrows():
        hteam = clean_team_name(row.get("hteam"))
        ateam = clean_team_name(row.get("ateam"))
        hprob = float(row.get("hprop_num"))

        key = (hteam, ateam)
        if key not in matchup_probs:
            matchup_probs[key] = []
        matchup_probs[key].append(hprob)

    # Calculate average probability across models for each game
    consensus_probs = {}
    for (hteam, ateam), prob_list in matchup_probs.items():
        avg_hprob = sum(prob_list) / len(prob_list)
        consensus_probs[(hteam, ateam)] = avg_hprob

    return consensus_probs

# -------------------------------------------------------------------
# EV Calculation Engine
# -------------------------------------------------------------------
def process_sportsbet_odds(odds_data, tips_df, min_win_prob, min_ev_pct, max_ev_pct):
    rows = []
    matchup_model_probs = build_matchup_probabilities(tips_df)

    for game in odds_data:
        home_clean = clean_team_name(game.get("home_team"))
        away_clean = clean_team_name(game.get("away_team"))
        
        commence_dt = pd.to_datetime(game.get("commence_time")).tz_convert("Australia/Melbourne")
        kickoff_str = commence_dt.strftime("%a %d %b, %I:%M %p")

        # Lookup average Squiggle model win probability for this specific matchup
        h_model_prob = matchup_model_probs.get((home_clean, away_clean), None)
        
        for bookmaker in game.get("bookmakers", []):
            if bookmaker.get("key").lower() != TARGET_BOOKMAKER:
                continue
                
            bm_title = bookmaker.get("title")
            for market in bookmaker.get("markets", []):
                mkt_key = market.get("key")
                
                mkt_name = "Head to Head"
                if mkt_key == "spreads":
                    mkt_name = "Line / Spread"
                elif mkt_key == "totals":
                    mkt_name = "Total Points"

                for outcome in market.get("outcomes", []):
                    team_or_type = outcome.get("name")
                    clean_target = clean_team_name(team_or_type)
                    price = outcome.get("price", 1.0)
                    point = outcome.get("point", None)
                    
                    target_desc = team_or_type
                    if point is not None:
                        target_desc = f"{team_or_type} ({'+' if point > 0 else ''}{point})"
                    
                    # Estimate Model Win Probability
                    if mkt_key == "h2h":
                        if h_model_prob is not None:
                            if clean_target == home_clean:
                                model_prob = h_model_prob
                            elif clean_target == away_clean:
                                model_prob = 1.0 - h_model_prob
                            else:
                                model_prob = 1.0 / price
                        else:
                            model_prob = 1.0 / price
                    else:
                        # Baseline assumption for spread/total markets
                        model_prob = 0.52

                    # Calculate Expected Value
                    ev = (model_prob * price) - 1.0
                    ev_pct = round(ev * 100, 1)
                    win_prob_pct = round(model_prob * 100, 1)
                    
                    # Check Recommendation Criteria
                    is_recommended = (
                        ev_pct >= min_ev_pct and 
                        ev_pct <= max_ev_pct and 
                        win_prob_pct >= min_win_prob
                    )
                    
                    rows.append({
                        "commence_dt": commence_dt,
                        "Kickoff": kickoff_str,
                        "Matchup": f"{home_clean} vs {away_clean}",
                        "Bookmaker": bm_title,
                        "Market": mkt_name,
                        "Selection": target_desc,
                        "Odds": f"${price:.2f}",
                        "Model Win Prob": f"{win_prob_pct}%",
                        "Expected Value (EV)": f"{'+' if ev_pct > 0 else ''}{ev_pct}%",
                        "EV_raw": ev,
                        "win_prob_raw": win_prob_pct,
                        "Recommendation": "✅ RECOMMENDED VALUE BET" if is_recommended else "❌ No Value"
                    })
    
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(by=["commence_dt", "EV_raw"], ascending=[True, False])
        df = df.drop(columns=["commence_dt", "EV_raw", "win_prob_raw"])
    return df

# -------------------------------------------------------------------
# Dashboard UI & Risk Controls
# -------------------------------------------------------------------
st.title("🏉 Sportsbet AFL Smart Bet Finder")
st.caption("Live Sportsbet odds matched against Squiggle consensus model predictions.")

st.sidebar.header("Model & Risk Controls")

if st.sidebar.button("🔄 Force Refresh Data"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")

# Customizable Risk Sliders
min_win_prob = st.sidebar.slider(
    "Min Model Win Probability (%)", 
    min_value=5, max_value=60, value=15, step=5,
    help="Filters out extreme underdogs below this win chance."
)

min_ev_pct = st.sidebar.slider(
    "Min Expected Value (+EV %)", 
    min_value=-5.0, max_value=15.0, value=0.0, step=0.5,
    help="Minimum mathematical edge required to trigger a recommendation."
)

max_ev_pct = st.sidebar.slider(
    "Max Expected Value (+EV %)", 
    min_value=10.0, max_value=200.0, value=50.0, step=5.0,
    help="Filters out abnormal data glitches."
)

st.sidebar.markdown("---")

# Fetch Data
with st.spinner("Fetching Sportsbet odds and Squiggle consensus model data..."):
    odds_raw, odds_err = fetch_sportsbet_odds(API_KEY)
    tips_df, tips_err = fetch_squiggle_tips(year=2026)

if odds_err:
    st.error(f"Error fetching odds: {odds_err}")
    st.stop()

if not odds_raw:
    st.warning("No Sportsbet odds available at this moment.")
    st.stop()

# Generate DataFrame
df = process_sportsbet_odds(odds_raw, tips_df, min_win_prob, min_ev_pct, max_ev_pct)

if not df.empty:
    available_markets = list(df["Market"].unique())
    selected_markets = st.sidebar.multiselect("Select Betting Markets:", options=available_markets, default=available_markets)
    only_value = st.sidebar.checkbox("Show Only Recommended Value Bets (+EV)", value=False)
    
    filtered_df = df[df["Market"].isin(selected_markets)]
    if only_value:
        filtered_df = filtered_df[filtered_df["Recommendation"].str.contains("RECOMMENDED")]
    
    st.subheader(f"Upcoming Matches & Sportsbet Markets ({len(filtered_df)} bets listed)")
    st.dataframe(filtered_df, use_container_width=True)
else:
    st.info("No matching odds available.")
