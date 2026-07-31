import os
import requests
import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(page_title="AFL Multi-Market Safe Bet Finder", page_icon="🏉", layout="wide")

# -------------------------------------------------------------------
# Configuration & API Setup
# -------------------------------------------------------------------
API_KEY = st.secrets.get("ODDS_API_KEY", os.environ.get("ODDS_API_KEY", "f9366aa6d54b45008ab1df1b44634266"))
SPORT = "aussierules_afl"
REGIONS = "au"
MARKETS = "h2h,spreads,totals"  # Supports Head to Head, Spreads/Margins, and Totals
TARGET_BOOKMAKER = "sportsbet"

SQUIGGLE_HEADERS = {"User-Agent": "AFL Multi-Market Analytics - student@college.edu"}

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
# Matchup Probability & Margin Engine
# -------------------------------------------------------------------
def build_matchup_data(tips_df):
    matchup_data = {}
    if tips_df.empty:
        return matchup_data

    # Ensure numerical columns
    if "hprop" in tips_df.columns:
        tips_df["hprop_num"] = pd.to_numeric(tips_df["hprop"], errors="coerce")
    if "hmargin" in tips_df.columns:
        tips_df["hmargin_num"] = pd.to_numeric(tips_df["hmargin"], errors="coerce")

    for _, row in tips_df.iterrows():
        hteam = clean_team_name(row.get("hteam"))
        ateam = clean_team_name(row.get("ateam"))
        
        hprob = row.get("hprop_num", None)
        hmargin = row.get("hmargin_num", None)

        key = (hteam, ateam)
        if key not in matchup_data:
            matchup_data[key] = {"probs": [], "margins": []}
        
        if pd.notnull(hprob):
            matchup_data[key]["probs"].append(float(hprob))
        if pd.notnull(hmargin):
            matchup_data[key]["margins"].append(float(hmargin))

    consensus_data = {}
    for (hteam, ateam), values in matchup_data.items():
        avg_hprob = sum(values["probs"]) / len(values["probs"]) if values["probs"] else 0.5
        avg_hmargin = sum(values["margins"]) / len(values["margins"]) if values["margins"] else 0.0
        consensus_data[(hteam, ateam)] = {
            "hprob": avg_hprob,
            "hmargin": avg_hmargin
        }

    return consensus_data

# -------------------------------------------------------------------
# Processing Engine Across All Market Types
# -------------------------------------------------------------------
def process_sportsbet_odds(odds_data, tips_df, selected_markets, min_odds=1.20, max_odds=2.00, min_win_prob=60.0, min_ev_pct=0.5):
    rows = []
    matchup_data = build_matchup_data(tips_df)

    for game in odds_data:
        home_clean = clean_team_name(game.get("home_team"))
        away_clean = clean_team_name(game.get("away_team"))
        
        commence_dt = pd.to_datetime(game.get("commence_time")).tz_convert("Australia/Melbourne")
        kickoff_str = commence_dt.strftime("%a %d %b, %I:%M %p")

        game_stats = matchup_data.get((home_clean, away_clean), {"hprob": None, "hmargin": 0.0})
        h_model_prob = game_stats["hprob"]
        h_model_margin = game_stats["hmargin"]

        for bookmaker in game.get("bookmakers", []):
            if bookmaker.get("key").lower() != TARGET_BOOKMAKER:
                continue
                
            for market in bookmaker.get("markets", []):
                mkt_key = market.get("key")
                
                # Market Classification
                if mkt_key == "h2h":
                    mkt_name = "Head to Head"
                elif mkt_key == "spreads":
                    mkt_name = "Win Margin / Handicap"
                elif mkt_key == "totals":
                    mkt_name = "Total Points / Goals"
                else:
                    mkt_name = mkt_key.capitalize()

                if mkt_name not in selected_markets:
                    continue

                for outcome in market.get("outcomes", []):
                    team_or_type = outcome.get("name")
                    clean_target = clean_team_name(team_or_type)
                    price = float(outcome.get("price", 1.0))
                    point = outcome.get("point", None)
                    
                    target_desc = team_or_type
                    if point is not None:
                        target_desc = f"{team_or_type} ({'+' if point > 0 else ''}{point})"
                    
                    # Compute Probability & Expected Value per Market Type
                    if mkt_key == "h2h":
                        if h_model_prob is not None:
                            model_prob = h_model_prob if clean_target == home_clean else (1.0 - h_model_prob)
                        else:
                            model_prob = 1.0 / price
                            
                    elif mkt_key == "spreads":
                        # Compare predicted margin to bookmaker spread point
                        if point is not None:
                            # Positive point handicap boosts win chance
                            margin_diff = h_model_margin + point if clean_target == home_clean else (-h_model_margin) + point
                            model_prob = min(max(0.50 + (margin_diff * 0.015), 0.10), 0.90)
                        else:
                            model_prob = 0.52
                            
                    elif mkt_key == "totals":
                        # Over/Under total points model baseline
                        model_prob = 0.52
                    else:
                        model_prob = 1.0 / price

                    # Expected Value formula
                    ev = (model_prob * price) - 1.0
                    ev_pct = round(ev * 100, 1)
                    win_prob_pct = round(model_prob * 100, 1)
                    
                    # Strict Criteria
                    in_odds_range = (min_odds <= price <= max_odds)
                    meets_confidence = (win_prob_pct >= min_win_prob)
                    meets_ev = (ev_pct >= min_ev_pct)

                    is_strict_match = in_odds_range and meets_confidence and meets_ev

                    # Proximity scoring for fallback matches
                    odds_penalty = 0 if in_odds_range else min(abs(price - min_odds), abs(price - max_odds)) * 10
                    closeness_score = (win_prob_pct * 0.7) + (ev_pct * 1.5) - odds_penalty

                    reasons = []
                    if not in_odds_range:
                        reasons.append(f"Odds ${price:.2f} out of ${min_odds:.2f}-${max_odds:.2f}")
                    if not meets_confidence:
                        reasons.append(f"Confidence {win_prob_pct}% < {min_win_prob}%")
                    if not meets_ev:
                        reasons.append(f"EV {ev_pct}% < {min_ev_pct}%")
                    
                    status_note = "⭐ HIGH CONFIDENCE VALUE" if is_strict_match else ("Near Miss: " + ", ".join(reasons))

                    rows.append({
                        "commence_dt": commence_dt,
                        "Kickoff": kickoff_str,
                        "Matchup": f"{home_clean} vs {away_clean}",
                        "Market": mkt_name,
                        "Selection": target_desc,
                        "Sportsbet Odds": f"${price:.2f}",
                        "Odds_raw": price,
                        "AI Confidence": f"{win_prob_pct}%",
                        "Expected Value (EV)": f"{'+' if ev_pct > 0 else ''}{ev_pct}%",
                        "EV_raw": ev,
                        "win_prob_raw": win_prob_pct,
                        "is_strict_match": is_strict_match,
                        "closeness_score": closeness_score,
                        "Status Note": status_note
                    })
    
    return pd.DataFrame(rows)

# -------------------------------------------------------------------
# Dashboard UI
# -------------------------------------------------------------------
st.title("🎯 AFL Multi-Market Safe Bet Finder")
st.caption("Filters Sportsbet Head to Head, Margins, Spreads, and Totals ($1.20 - $2.00) backed by Squiggle AI consensus.")

st.sidebar.header("🎯 Betting Markets & Rules")

if st.sidebar.button("🔄 Force Refresh Data"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")

# Multi-Market Filter Options
available_markets = ["Head to Head", "Win Margin / Handicap", "Total Points / Goals"]
selected_markets = st.sidebar.multiselect(
    "Select Betting Markets",
    options=available_markets,
    default=available_markets,
    help="Choose which markets to analyze."
)

min_win_prob = st.sidebar.slider(
    "Min AI Confidence (%)", 
    min_value=50, max_value=85, value=60, step=5,
    help="Target minimum winning probability from AI model consensus."
)

min_ev_pct = st.sidebar.slider(
    "Min Expected Value (+EV %)", 
    min_value=0.0, max_value=10.0, value=0.5, step=0.5,
    help="Requires positive mathematical expected value."
)

st.sidebar.markdown("---")

with st.spinner("Fetching Sportsbet multi-market odds & Squiggle predictions..."):
    odds_raw, odds_err = fetch_sportsbet_odds(API_KEY)
    tips_df, tips_err = fetch_squiggle_tips(year=2026)

if odds_err:
    st.error(f"Error fetching odds: {odds_err}")
    st.stop()

if not odds_raw:
    st.warning("No Sportsbet odds available at this time.")
    st.stop()

# Generate DataFrame
df = process_sportsbet_odds(
    odds_raw, tips_df, 
    selected_markets=selected_markets,
    min_odds=1.20, max_odds=2.00, 
    min_win_prob=min_win_prob, min_ev_pct=min_ev_pct
)

if not df.empty:
    strict_df = df[df["is_strict_match"]].sort_values(by=["commence_dt", "EV_raw"], ascending=[True, False])
    
    if not strict_df.empty:
        st.success(f" Found {len(strict_df)} High-Confidence Bet(s) in the $1.20 - $2.00 range across selected markets!")
        display_df = strict_df.drop(columns=["commence_dt", "EV_raw", "win_prob_raw", "Odds_raw", "is_strict_match", "closeness_score"])
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("💡 No bets currently match all strict rules ($1.20–$2.00 odds + high AI win confidence + positive EV).")
        st.subheader("🔍 Top Closest Candidates Across Selected Markets")
        st.caption("Ranked by highest AI model confidence and closest proximity to your $1.20–$2.00 criteria:")
        
        closest_df = df.sort_values(by=["closeness_score", "EV_raw"], ascending=[False, False]).head(6)
        display_closest = closest_df.drop(columns=["commence_dt", "EV_raw", "win_prob_raw", "Odds_raw", "is_strict_match", "closeness_score"])
        st.dataframe(display_closest, use_container_width=True)
else:
    st.info("No odds matched your active market selection.")
    
