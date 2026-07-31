import os
import requests
import itertools
import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(page_title="AFL Safe Bet & Realistic SGM Finder", page_icon="🏉", layout="wide")

# -------------------------------------------------------------------
# Configuration & API Setup
# -------------------------------------------------------------------
API_KEY = st.secrets.get("ODDS_API_KEY", os.environ.get("ODDS_API_KEY", "f9366aa6d54b45008ab1df1b44634266"))
SPORT = "aussierules_afl"
REGIONS = "au"
FEATURED_MARKETS = "h2h,spreads,totals"
PROP_MARKETS = "player_disposals"
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
def fetch_sportsbet_odds(api_key: str, include_props=True):
    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds/"
    params = {
        "apiKey": api_key,
        "regions": REGIONS,
        "markets": FEATURED_MARKETS,
        "bookmakers": TARGET_BOOKMAKER,
        "dateFormat": "iso",
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        games = response.json()
    except requests.exceptions.RequestException as e:
        return None, str(e)

    if include_props and games:
        for game in games:
            event_id = game.get("id")
            if not event_id:
                continue
            
            event_url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/events/{event_id}/odds"
            event_params = {
                "apiKey": api_key,
                "regions": REGIONS,
                "markets": PROP_MARKETS,
                "bookmakers": TARGET_BOOKMAKER,
                "dateFormat": "iso",
            }
            try:
                e_resp = requests.get(event_url, params=event_params, timeout=5)
                if e_resp.status_code == 200:
                    e_data = e_resp.json()
                    e_bookmakers = e_data.get("bookmakers", [])
                    
                    for bm in e_bookmakers:
                        if bm.get("key").lower() == TARGET_BOOKMAKER:
                            for game_bm in game.get("bookmakers", []):
                                if game_bm.get("key").lower() == TARGET_BOOKMAKER:
                                    game_bm["markets"].extend(bm.get("markets", []))
            except Exception:
                pass

    return games, None

# -------------------------------------------------------------------
# Model Consensus Engine
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
# Processing Engine (Current Round Window + Exact Singles Logic)
# -------------------------------------------------------------------
def process_sportsbet_odds(odds_data, tips_df, selected_markets, min_win_prob=60.0):
    rows = []
    matchup_data = build_matchup_data(tips_df)

    # Filter strictly for Current Round / Current Week (0 to 7 days window)
    now_dt = pd.Timestamp.now(tz="Australia/Melbourne")
    week_limit_dt = now_dt + pd.Timedelta(days=7)

    for game in odds_data:
        commence_dt = pd.to_datetime(game.get("commence_time")).tz_convert("Australia/Melbourne")
        
        # Enforce current week / current round window
        if not (now_dt <= commence_dt <= week_limit_dt):
            continue

        home_clean = clean_team_name(game.get("home_team"))
        away_clean = clean_team_name(game.get("away_team"))
        game_id = f"{home_clean} vs {away_clean}"
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
                    team_or_type = outcome.get("name", "")
                    clean_target = clean_team_name(team_or_type)
                    price = float(outcome.get("price", 1.0))
                    point = outcome.get("point", None)
                    description = outcome.get("description", "")
                    
                    if price <= 1.0:
                        continue

                    market_implied_prob = 1.0 / price
                    
                    if mkt_name == "Player Disposals":
                        player = description if description else team_or_type
                        if point is not None:
                            val = int(point) if float(point).is_integer() else point
                            prefix = "Over " if "Over" in team_or_type or "Over" in description else ("Under " if "Under" in team_or_type or "Under" in description else "")
                            target_desc = f"{player} {val}+ Disposals" if float(point).is_integer() else f"{player} {prefix}{point} Disposals"
                        else:
                            target_desc = f"{player} Disposals"
                        team_assoc = player
                    elif mkt_name == "Total Points / Goals":
                        prefix = "Over " if "Over" in team_or_type else ("Under " if "Under" in team_or_type else "")
                        target_desc = f"{prefix}{point} Total Points" if point else team_or_type
                        team_assoc = "Game Total"
                    elif point is not None:
                        target_desc = f"{team_or_type} ({'+' if point > 0 else ''}{point})"
                        team_assoc = clean_target
                    else:
                        target_desc = team_or_type
                        team_assoc = clean_target
                    
                    if mkt_key == "h2h":
                        if h_model_prob is not None:
                            raw_model_prob = h_model_prob if clean_target == home_clean else (1.0 - h_model_prob)
                            model_prob = min(raw_model_prob, market_implied_prob * 1.25)
                        else:
                            model_prob = market_implied_prob
                    elif mkt_key == "spreads":
                        if point is not None:
                            margin_diff = h_model_margin + point if clean_target == home_clean else (-h_model_margin) + point
                            model_prob = min(max(0.50 + (margin_diff * 0.015), 0.10), 0.90)
                        else:
                            model_prob = market_implied_prob
                    elif mkt_name == "Player Disposals":
                        model_prob = min(market_implied_prob * 1.05, 0.92)
                    else:
                        model_prob = market_implied_prob

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
                        "home_team": home_clean,
                        "away_team": away_clean,
                        "commence_dt": commence_dt,
                        "Kickoff": kickoff_str,
                        "Matchup": game_id,
                        "Market": mkt_name,
                        "Selection": target_desc,
                        "team_assoc": team_assoc,
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
# Conflict Check
# -------------------------------------------------------------------
def are_legs_compatible(leg1, leg2):
    if leg1["Market"] in ["Head to Head", "Win Margin / Handicap"] and leg2["Market"] in ["Head to Head", "Win Margin / Handicap"]:
        if leg1["team_assoc"] != leg2["team_assoc"]:
            return False

    if leg1["Market"] == "Total Points / Goals" and leg2["Market"] == "Total Points / Goals":
        if ("Over" in leg1["Selection"] and "Under" in leg2["Selection"]) or ("Under" in leg1["Selection"] and "Over" in leg2["Selection"]):
            return False

    if leg1["Selection"] == leg2["Selection"]:
        return False

    return True

# -------------------------------------------------------------------
# Dual SGM Engine (Generates Exactly 2 SGMs per Current Round Game)
# -------------------------------------------------------------------
def generate_two_sgms_per_game(df, target_min_odds=1.65, target_max_odds=2.35):
    game_multis = []
    if df.empty:
        return game_multis

    for game_id, group in df.groupby("Game_ID"):
        kickoff_time = group.iloc[0]["Kickoff"]

        # Helper evaluator function to construct a multi targeting ~$2.00 odds from given candidate legs
        def find_best_multi(legs_list, multi_type_name):
            if len(legs_list) < 2:
                # Fallback: take top selections from whole game pool
                legs_list = group.sort_values("win_prob_num", ascending=False).drop_duplicates(subset=["Selection"]).to_dict("records")

            if len(legs_list) < 2:
                return None

            all_combos = []
            for k_legs in range(2, min(6, len(legs_list) + 1)):
                for combo in itertools.combinations(legs_list, k_legs):
                    compatible = True
                    for i_idx in range(len(combo)):
                        for j_idx in range(i_idx + 1, len(combo)):
                            if not are_legs_compatible(combo[i_idx], combo[j_idx]):
                                compatible = False
                                break
                        if not compatible:
                            break
                    if not compatible:
                        continue

                    comb_odds = 1.0
                    comb_prob = 1.0
                    for leg in combo:
                        comb_odds *= leg["Odds_num"]
                        comb_prob *= (leg["win_prob_num"] / 100.0)

                    comb_prob_pct = round(comb_prob * 100, 1)
                    dist_from_target = abs(comb_odds - 2.00)

                    combo_score = (comb_prob_pct * 3.0) - (dist_from_target * 25.0)

                    formatted_legs = [
                        f"• **{leg['Selection']}** ({leg['Market']} @ ${leg['Odds_num']:.2f}) — *AI Prob: {leg['win_prob_num']}%*"
                        for leg in combo
                    ]

                    all_combos.append({
                        "Game": game_id,
                        "Kickoff": kickoff_time,
                        "Type": multi_type_name,
                        "Leg Count": f"{len(combo)} Legs",
                        "Combined Odds": f"${comb_odds:.2f}",
                        "comb_odds_num": comb_odds,
                        "Est. Combined Win Prob": f"{comb_prob_pct}%",
                        "dist_from_target": dist_from_target,
                        "score": combo_score,
                        "Legs": formatted_legs
                    })

            if all_combos:
                in_range = [c for c in all_combos if target_min_odds <= c["comb_odds_num"] <= target_max_odds]
                if in_range:
                    return max(in_range, key=lambda x: x["score"])
                else:
                    return min(all_combos, key=lambda x: x["dist_from_target"])
            return None

        # -------------------------------------------------------------
        # MULTI 1: Safe Cushion & Milestone Disposals (Handicaps + 15+/20+/25+)
        # -------------------------------------------------------------
        cushion_disp_legs = group[
            (group["Market"].isin(["Win Margin / Handicap", "Player Disposals"])) &
            (~group["Selection"].str.contains("Over ", na=False)) &
            (~group["Selection"].str.contains("Under ", na=False))
        ].drop_duplicates(subset=["Selection"]).to_dict("records")

        multi_1 = find_best_multi(cushion_disp_legs, "🛡️ Multi 1: Safe Cushion & Milestone Disposals")

        # -------------------------------------------------------------
        # MULTI 2: Match Result & Game Totals (H2H + Over/Under Lines)
        # -------------------------------------------------------------
        h2h_totals_legs = group[
            group["Market"].isin(["Head to Head", "Total Points / Goals", "Win Margin / Handicap"])
        ].drop_duplicates(subset=["Selection"]).to_dict("records")

        multi_2 = find_best_multi(h2h_totals_legs, "⚡ Multi 2: Match Result & Game Totals")

        game_multis.append({
            "Game": game_id,
            "Kickoff": kickoff_time,
            "Multi_1": multi_1,
            "Multi_2": multi_2
        })

    return game_multis

# -------------------------------------------------------------------
# Dashboard Interface
# -------------------------------------------------------------------
st.title("🎯 AFL Safe Bet & Realistic SGM Finder")
st.caption("Analyzes Sportsbet odds & Squiggle AI models to identify high-probability singles and realistic SGMs.")

st.sidebar.header("⚙️ Controls")

if st.sidebar.button("🔄 Refresh Data"):
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
    "Min AI Win Prob (%)", 
    min_value=50, max_value=80, value=60, step=5
)

st.sidebar.markdown("---")

include_player_props = "Player Disposals" in selected_markets

with st.spinner("Fetching Sportsbet odds & Squiggle predictions..."):
    odds_raw, odds_err = fetch_sportsbet_odds(API_KEY, include_props=include_player_props)
    tips_df, tips_err = fetch_squiggle_tips(year=2026)

if odds_err:
    st.error(f"Error fetching odds: {odds_err}")
    st.stop()

if not odds_raw:
    st.warning("No Sportsbet odds available at the moment.")
    st.stop()

df = process_sportsbet_odds(odds_raw, tips_df, selected_markets=selected_markets, min_win_prob=min_win_prob)

tab_singles, tab_multis = st.tabs(["📊 High-Confidence Singles ($1.20–$2.00)", "🔥 Current Round SGMs (2 Options per Game)"])

# -------------------------------------------------------------------
# TAB 1: SINGLES (UNTOUCHED LOGIC)
# -------------------------------------------------------------------
with tab_singles:
    if not df.empty:
        strict_df = df[df["is_match"]].sort_values(by=["commence_dt", "win_prob_num"], ascending=[True, False])
        if not strict_df.empty:
            st.success(f" Found {len(strict_df)} High-Confidence Single Bet(s) for the current round!")
            display_df = strict_df[["Kickoff", "Matchup", "Market", "Selection", "Odds", "AI Win Prob", "Recommendation"]]
            st.dataframe(display_df, use_container_width=True)
        else:
            st.info("💡 No single bets currently match all strict target criteria ($1.20–$2.00 odds + high AI win probability).")
            st.subheader("🔍 Closest Single Bet Candidates")
            closest_df = df.sort_values(by=["score", "win_prob_num"], ascending=[False, False]).head(5)
            display_closest = closest_df[["Kickoff", "Matchup", "Market", "Selection", "Odds", "AI Win Prob", "Recommendation"]]
            st.dataframe(display_closest, use_container_width=True)
    else:
        st.info("No current round AFL matches scheduled in the feed.")

# -------------------------------------------------------------------
# TAB 2: CURRENT ROUND SGMs (EXACTLY 2 PER GAME)
# -------------------------------------------------------------------
with tab_multis:
    st.subheader("🏉 Current Round SGMs (~$2.00 Target Return)")
    st.caption("Displays 2 tailored SGMs per match for every fixture this round, strictly bounded around $1.65 – $2.35 odds.")
    
    game_multis_list = generate_two_sgms_per_game(df, target_min_odds=1.65, target_max_odds=2.35)
    
    if game_multis_list:
        for g_data in game_multis_list:
            st.markdown(f"### 📍 {g_data['Game']} ({g_data['Kickoff']})")
            
            col_m1, col_m2 = st.columns(2)
            
            with col_m1:
                m1 = g_data.get("Multi_1")
                if m1:
                    with st.expander(f"🛡️ **SGM 1: Safe Cushion & Disposals** ({m1['Leg Count']} @ **{m1['Combined Odds']}**)", expanded=True):
                        st.write("**Recommended SGM Legs:**")
                        for leg in m1["Legs"]:
                            st.markdown(leg)
                        st.metric("Total Multi Payout", m1["Combined Odds"])
                        st.metric("Est. Combined Model Win Prob", m1["Est. Combined Win Prob"])
                else:
                    st.info("Insufficient market options for SGM 1.")
                    
            with col_m2:
                m2 = g_data.get("Multi_2")
                if m2:
                    with st.expander(f"⚡ **SGM 2: H2H & Match Totals** ({m2['Leg Count']} @ **{m2['Combined Odds']}**)", expanded=True):
                        st.write("**Recommended SGM Legs:**")
                        for leg in m2["Legs"]:
                            st.markdown(leg)
                        st.metric("Total Multi Payout", m2["Combined Odds"])
                        st.metric("Est. Combined Model Win Prob", m2["Est. Combined Win Prob"])
                else:
                    st.info("Insufficient market options for SGM 2.")
            
            st.markdown("---")
    else:
        st.info("No current round AFL games available in the current odds feed.")
        
