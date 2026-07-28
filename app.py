import streamlit as st
import pandas as pd

st.set_page_config(page_title="AFL +EV Bet Finder", layout="wide")

st.title("🏈 Automated AFL +EV Pre-Game Edge Finder")
st.caption("Live game suggestions generated automatically before bounce-down.")

try:
    df = pd.read_csv("latest_bets.csv")
    
    min_ev = st.slider("Filter Minimum Expected Value (+EV %)", 0.0, 30.0, 8.0)
    filtered_df = df[df['EV_Percentage'] >= min_ev]

    st.subheader("Recommended Value Plays")
    st.dataframe(
        filtered_df[['Match', 'Market', 'Selection', 'Line', 'Bookie_Odds', 'Model_Prob', 'EV_Percentage']],
        use_container_width=True
    )
except FileNotFoundError:
    st.info("No active game data found yet. Updates run automatically on schedule.")
