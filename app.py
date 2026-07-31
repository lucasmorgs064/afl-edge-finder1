import os
import requests
import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(page_title="AFL Safe Bet & Multi Finder", page_icon="🏉", layout="wide")

# -------------------------------------------------------------------
# Configuration & API Setup
# -------------------------------------------------------------------
API_KEY = st.secrets.get("ODDS_API_KEY", os.environ.get("ODDS_API_KEY", "f9366aa6d54b45008ab1df1b44634266"))
SPORT = "aussierules_afl"
REGIONS = "au"
# Added player_disposals to requested markets
MARKETS = "h2h,spreads,totals,player_disposals"
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
# Model Data Engine
# -------------------------------------------------------------------
def build_matchup_data(tips_df):
    matchup_data = {}
    if tips_df.empty:
        return matchup_data

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
# Processing Engine: Singles & Multi Candidates
# -------------------------------------------------------------------
def process_sportsbet_odds(odds_data, tips_df, selected_markets, min_win_prob=60.0):
    rows = []
    matchup_data = build_matchup_data(tips_df)

    for game in odds_data:
        home_clean = clean_team_name(game.get("home_team"))
        away_clean = clean_team_name(game.get("away_team"))
        game_id = f"{home_clean} vs {away_clean}"
        
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
                
                if mkt_key == "h2h":
                    mkt_name = "Head to Head"
                elif mkt_key == "spreads":
                    mkt_name = "Win Margin / Handicap"
                elif mkt_key == "totals":
                    mkt_name = "Total Points / Goals"
                elif "player_disposals" in mkt_key:
                    mkt_name = "Player Disposals"
                else:
                    mkt_name = mkt_key.replace("_", " ").title()

                if mkt_name not in selected_markets:
                    continue

                for outcome in market.get("outcomes", []):
                    team_or_type = outcome.get("name")
                    clean_target = clean_team_name(team_or_type)
                    price = float(outcome.get("price", 1.0))
                    point = outcome.get("point", None)
                    description = outcome.get("description", "")
                    
                    # Format selection string
                    if mkt_name == "Player Disposals":
                        player = description if description else team_or_type
                        line_val = f" {point}+" if point else ""
                        target_desc = f"{player}{line_val} Disposals"
                    elif point is not None:
                        target_desc = f"{team_or_type} ({'+' if point > 0 else ''}{point})"
                    else:
                        target_desc = team_or_type
                    
                    # Win probability estimation
                    if mkt_key == "h2h":
                        if h_model_prob is not None:
                            model_prob = h_model_prob if clean_target == home_clean else (1.0 - h_model_prob)
                        else:
                            model_prob = 1.0 / price
                    elif mkt_key == "spreads":
                        if point is not None:
                            margin_diff = h_model_margin + point if clean_target == home_clean else (-h_model_margin) + point
                            model_prob = min(max(0.50 + (margin_diff * 0.015), 0.10), 0.90)
                        else:
                            model_prob = 0.52
                    elif mkt_name == "Player Disposals":
                        # High baseline for low disposal thresholds (e.g., 15+ or 20+ disposals)
                        model_prob = min(max((1.0 / price) * 1.08, 0.55), 0.88)
                    else:
                        model_prob = 1.0 / price

                    win_prob_pct = round(model_prob * 100, 1)
                    
                    in_safe_range = (1.20 <= price <= 2.00)

                    if in_safe_range and win_prob_pct >= 65.0:
                        rec_rating = "⭐⭐⭐ HIGH CONFIDENCE"
                        is_match = True
                    elif in_safe_range and win_prob_pct >= min_win_prob:
                        rec_rating = "⭐⭐ GOOD VALUE"
                        is_match = True
                    else:
                        rec_rating = "⭐ LEAN / NEAR MISS"
                        is_match = False

                    score = win_prob_pct - (abs(price - 1.50) * 10)

                    rows.append({
                        "Game_ID": game_id,
                        "commence_dt": commence_dt,
                        "Kickoff": kickoff_str,
                        "Matchup": game_id,
                        "Market": mkt_name,
                        "Selection": target_desc,
                        "Odds": f"${price:.2f}",
                        "Odds_num": price,
                        "AI Win Prob": f"{win_prob_pct}%",
                        "win_prob_num": win_prob_pct,
                        "Recommendation": rec_rating,
                        "is_match": is_match,
                        "score": score
                    })
    
    return pd.DataFrame(rows)

# -------------------------------------------------------------------
# Per-Game 3-Leg Same-Game Multi Generator
# -------------------------------------------------------------------
def generate_game_multis(df):
    game_multis = []
    if df.empty:
        return game_multis

    for game_id, group in df.groupby("Game_ID"):
        # Sort legs by highest AI confidence and best score
        sorted_legs = group.sort_values(by=["win_prob_num", "score"], ascending=[False, False])
        
        # Deduplicate legs with identical selections
        unique_legs = sorted_legs.drop_duplicates(subset=["Selection"]).head(3)
        
        if len(unique_legs) == 3:
            combined_odds = 1.0
            combined_prob = 1.0
            legs_list = []

            for _, leg in unique_legs.iterrows():
                combined_odds *= leg["Odds_num"]
                combined_prob *= (leg["win_prob_num"] / 100.0)
                legs_list.append(f"• **{leg['Selection']}** ({leg['Market']} @ ${leg['Odds_num']:.2f}) - *AI Win Prob: {leg['win_prob_num']}%*")

            combined_prob_pct = round(combined_prob * 100, 1)

            game_multis.append({
                "Game": game_id,
                "Kickoff": unique_legs.iloc[0]["Kickoff"],
                "Combined Odds": f"${combined_odds:.2f}",
                "Est. Combined Win Prob": f"{combined_prob_pct}%",
                "Legs": legs_list
            })

    return game_multis

# -------------------------------------------------------------------
# Dashboard Interface
# -------------------------------------------------------------------
st.title("🎯 AFL High-Confidence Bet & Multi Dashboard")
st.caption("Analyzes Sportsbet Head to Head, Margins, Totals, and Player Disposals using Squiggle AI consensus.")

st.sidebar.header("⚙️ Controls")

if st.sidebar.button("🔄 Refresh Odds"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")

available_markets = ["Head to Head", "Win Margin / Handicap", "Total Points / Goals", "Player Disposals"]
selected_markets = st.sidebar.multiselect(
    "Active Betting Markets",
    options=available_markets,
    default=available_markets
)

min_win_prob = st.sidebar.slider(
    "Minimum AI Win Prob (%)", 
    min_value=50, max_value=80, value=60, step=5
)

st.sidebar.markdown("---")

with st.spinner("Fetching Sportsbet odds, player props & Squiggle predictions..."):
    odds_raw, odds_err = fetch_sportsbet_odds(API_KEY)
    tips_df, tips_err = fetch_squiggle_tips(year=2026)

if odds_err:
    st.error(f"Error: {odds_err}")
    st.stop()

if not odds_raw:
    st.warning("No Sportsbet odds available at the moment.")
    st.stop()

df = process_sportsbet_odds(odds_raw, tips_df, selected_markets=selected_markets, min_win_prob=min_win_prob)

# Main Navigation Tabs
tab_singles, tab_multis = st.tabs(["📊 Single Safe Bets ($1.20 - $2.00)", "🔥 Recommended 3-Leg Multis (By Game)"])

with tab_singles:
    if not df.empty:
        strict_df = df[df["is_match"]].sort_values(by=["commence_dt", "win_prob_num"], ascending=[True, False])
        
        if not strict_df.empty:
            st.success(f" Found {len(strict_df)} High-Confidence Bet(s) in the $1.20 - $2.00 range!")
            display_df = strict_df[["Kickoff", "Matchup", "Market", "Selection", "Odds", "AI Win Prob", "Recommendation"]]
            st.dataframe(display_df, use_container_width=True)
        else:
            st.info("💡 No single bets currently match all strict target criteria ($1.20–$2.00 odds + high AI win probability).")
            st.subheader("🔍 Closest Single Bet Candidates")
            closest_df = df.sort_values(by=["score", "win_prob_num"], ascending=[False, False]).head(5)
            display_closest = closest_df[["Kickoff", "Matchup", "Market", "Selection", "Odds", "AI Win Prob", "Recommendation"]]
            st.dataframe(display_closest, use_container_width=True)
    else:
        st.info("No odds available for selected markets.")

with tab_multis:
    st.subheader("🏉 Recommended 3-Leg Same-Game Multis")
    st.caption("Automatically combines the 3 highest-confidence legs for each match on the slate:")
    
    multis = generate_game_multis(df)
    
    if multis:
        for multi in multis:
            with st.expander(f"📍 **{multi['Game']}** ({multi['Kickoff']}) — Combined Price: **{multi['Combined Odds']}**"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Recommended Legs:**")
                    for leg in multi["Legs"]:
                        st.markdown(leg)
                with col2:
                    st.metric("Total Multi Price", multi["Combined Odds"])
                    st.metric("Est. Combined Model Win Prob", multi["Est. Combined Win Prob"])
    else:
        st.info("Insufficient market legs available to construct 3-leg multis for upcoming games.")
