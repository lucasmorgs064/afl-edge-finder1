import os
import requests
import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(page_title="AFL High-Confidence Bet Finder", page_icon="🏉", layout="wide")

# -------------------------------------------------------------------
# Configuration & API Setup
# -------------------------------------------------------------------
API_KEY = st.secrets.get("ODDS_API_KEY", os.environ.get("ODDS_API_KEY", "f9366aa6d54b45008ab1df1b44634266"))
SPORT = "aussierules_afl"
REGIONS = "au"
MARKETS = "h2h,spreads"
TARGET_BOOKMAKER = "sportsbet"

SQUIGGLE_HEADERS = {"User-Agent": "AFL Safe Bet Analytics - student@college.edu"}

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
# Matchup Probability Engine
# -------------------------------------------------------------------
def build_matchup_probabilities(tips_df):
    matchup_probs = {}
    if tips_df.empty or "hprop" not in tips_df.columns:
        return matchup_probs

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

    consensus_probs = {}
    for (hteam, ateam), prob_list in matchup_probs.items():
        avg_hprob = sum(prob_list) / len(prob_list)
        consensus_probs[(hteam, ateam)] = avg_hprob

    return consensus_probs

# -------------------------------------------------------------------
# Processing Engine
# -------------------------------------------------------------------
def process_sportsbet_odds(odds_data, tips_df, min_odds, max_odds, min_win_prob, min_ev_pct):
    rows = []
    matchup_model_probs = build_matchup_probabilities(tips_df)

    for game in odds_data:
        home_clean = clean_team_name(game.get("home_team"))
        away_clean = clean_team_name(game.get("away_team"))
        
        commence_dt = pd.to_datetime(game.get("commence_time")).tz_convert("Australia/Melbourne")
        kickoff_str = commence_dt.strftime("%a %d %b, %I:%M %p")

        h_model_prob = matchup_model_probs.get((home_clean, away_clean), None)
        
        for bookmaker in game.get("bookmakers", []):
            if bookmaker.get("key").lower() != TARGET_BOOKMAKER:
                continue
                
            for market in bookmaker.get("markets", []):
                mkt_key = market.get("key")
                mkt_name = "Head to Head" if mkt_key == "h2h" else "Line / Spread"

                for outcome in market.get("outcomes", []):
                    team_or_type = outcome.get("name")
                    clean_target = clean_team_name(team_or_type)
                    price = float(outcome.get("price", 1.0))
                    point = outcome.get("point", None)
                    
                    target_desc = team_or_type
                    if point is not None:
                        target_desc = f"{team_or_type} ({'+' if point > 0 else ''}{point})"
                    
                    # Compute win probabilities
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
                        model_prob = 0.52

                    # Calculate Expected Value
                    ev = (model_prob * price) - 1.0
                    ev_pct = round(ev * 100, 1)
                    win_prob_pct = round(model_prob * 100, 1)
                    
                    # Target strict evaluation criteria
                    in_odds_range = (min_odds <= price <= max_odds)
                    meets_confidence = (win_prob_pct >= min_win_prob)
                    meets_ev = (ev_pct >= min_ev_pct)

                    is_strict_match = in_odds_range and meets_confidence and meets_ev

                    # Proximity/Closeness metric for fallback ranking
                    # Gives highest score to selections close to/inside target odds with strong win chance and EV
                    odds_penalty = 0 if in_odds_range else min(abs(price - min_odds), abs(price - max_odds)) * 10
                    closeness_score = (win_prob_pct * 0.6) + (ev_pct * 2.0) - odds_penalty

                    # Status reason for near-miss explanation
                    reasons = []
                    if not in_odds_range:
                        reasons.append(f"Odds ${price:.2f} outside ${min_odds:.2f}-${max_odds:.2f}")
                    if not meets_confidence:
                        reasons.append(f"Win Prob {win_prob_pct}% < {min_win_prob}%")
                    if not meets_ev:
                        reasons.append(f"EV {ev_pct}% < {min_ev_pct}%")
                    
                    status_note = "⭐ HIGH CONFIDENCE VALUE" if is_strict_match else ("Near Miss: " + ", ".join(reasons))

                    rows.append({
                        "commence_dt": commence_dt,
                        "Kickoff": kickoff_str,
                        "Matchup": f"{home_clean} vs {away_clean}",
                        "Market": mkt_name,
                        "Selection": target_desc,
                        "Odds": f"${price:.2f}",
                        "Odds_raw": price,
                        "Model Confidence": f"{win_prob_pct}%",
                        "Expected Value (EV)": f"{'+' if ev_pct > 0 else ''}{ev_pct}%",
                        "EV_raw": ev,
                        "win_prob_raw": win_prob_pct,
                        "is_strict_match": is_strict_match,
                        "closeness_score": closeness_score,
                        "Status / Reason": status_note
                    })
    
    return pd.DataFrame(rows)

# -------------------------------------------------------------------
# Dashboard UI
# -------------------------------------------------------------------
st.title("🎯 AFL Safe Bet & High-Confidence Dashboard")
st.caption("Filters Sportsbet odds for high-confidence favorites ($1.20 - $2.00) backed by Squiggle AI model consensus.")

st.sidebar.header("🎯 Safe Bet Parameters")

if st.sidebar.button("🔄 Force Refresh Data"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")

# Odds Window Selector
odds_range = st.sidebar.slider(
    "Target Odds Window ($)",
    min_value=1.05, max_value=3.00, value=(1.20, 2.00), step=0.05,
    help="Limits selections to safe favorite odds."
)

min_win_prob = st.sidebar.slider(
    "Min AI Model Confidence (%)", 
    min_value=50, max_value=85, value=60, step=5,
    help="Ensures the model predicts a strong likelihood of winning."
)

min_ev_pct = st.sidebar.slider(
    "Min Expected Value (+EV %)", 
    min_value=0.0, max_value=10.0, value=1.0, step=0.5,
    help="Ensures you get positive mathematical value."
)

st.sidebar.markdown("---")

# Fetch Data
with st.spinner("Fetching Sportsbet odds and AI consensus models..."):
    odds_raw, odds_err = fetch_sportsbet_odds(API_KEY)
    tips_df, tips_err = fetch_squiggle_tips(year=2026)

if odds_err:
    st.error(f"Error fetching odds: {odds_err}")
    st.stop()

if not odds_raw:
    st.warning("No Sportsbet odds currently available.")
    st.stop()

# Process Odds
df = process_sportsbet_odds(
    odds_raw, tips_df, 
    min_odds=odds_range[0], max_odds=odds_range[1], 
    min_win_prob=min_win_prob, min_ev_pct=min_ev_pct
)

if not df.empty:
    strict_df = df[df["is_strict_match"]].sort_values(by=["commence_dt", "EV_raw"], ascending=[True, False])
    
    if not strict_df.empty:
        st.success(f" Found {len(strict_df)} High-Confidence Value Bet(s) matching all target rules!")
        display_df = strict_df.drop(columns=["commence_dt", "EV_raw", "win_prob_raw", "Odds_raw", "is_strict_match", "closeness_score"])
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info(f"💡 No bets currently match **ALL** strict rules (${odds_range[0]:.2f}-${odds_range[1]:.2f} odds + {min_win_prob}% confidence + +{min_ev_pct}% EV).")
        st.subheader("🔍 Closest Candidate Bets On The Slate")
        st.caption("Here are the top candidates that came closest to your criteria, sorted by AI model confidence & EV:")
        
        # Fallback: Sort by closeness_score & EV
        closest_df = df.sort_values(by=["closeness_score", "EV_raw"], ascending=[False, False]).head(5)
        display_closest = closest_df.drop(columns=["commence_dt", "EV_raw", "win_prob_raw", "Odds_raw", "is_strict_match", "closeness_score"])
        st.dataframe(display_closest, use_container_width=True)
else:
    st.info("No odds available.")
