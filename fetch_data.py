import os
import pandas as pd
import requests

# Securely reads your key from GitHub Secrets
API_KEY = os.getenv("ODDS_API_KEY")

url = f"https://api.the-odds-api.com/v4/sports/aussierules_afl/odds/?apiKey={API_KEY}&regions=au&markets=totals,player_disposals"

# Sample structure outputting results to CSV for Streamlit
data = [
    {"Match": "Collingwood vs Geelong", "Market": "Total Game Points", "Selection": "UNDER", "Line": 171.5, "Bookie_Odds": 1.90, "Model_Prob": "62%", "EV_Percentage": 17.8},
    {"Match": "Collingwood vs Geelong", "Market": "Nick Daicos Disposals", "Selection": "UNDER", "Line": 30.5, "Bookie_Odds": 1.88, "Model_Prob": "58%", "EV_Percentage": 9.0}
]

df = pd.DataFrame(data)
df.to_csv("latest_bets.csv", index=False)
