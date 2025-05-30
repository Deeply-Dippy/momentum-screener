import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# Define tickers (expandable)
tickers = {
    "NVDA": {"name": "NVIDIA", "region": "US", "sector": "Technology"},
    "AAPL": {"name": "Apple", "region": "US", "sector": "Technology"},
    "BP.L": {"name": "BP", "region": "UK", "sector": "Energy"},
    "7203.T": {"name": "Toyota", "region": "Asia", "sector": "Automotive"},
    "ASML.AS": {"name": "ASML", "region": "EU", "sector": "Technology"},
}

st.set_page_config(page_title="Global Momentum Screener", layout="wide")
st.title("📈 Global Momentum Screener")

region_filter = st.sidebar.multiselect("Select Region(s)", options=["US", "UK", "EU", "Asia"], default=["US", "UK", "EU", "Asia"])
sector_filter = st.sidebar.multiselect("Select Sector(s)", options=list(set([d["sector"] for d in tickers.values()])), default=[])
timeframe = st.sidebar.radio("Timeframe", ["1 Week", "1 Month"])

today = datetime.today()
start_date = today - timedelta(days=7 if timeframe == "1 Week" else 30)
st.write(f"Showing data from **{start_date.date()}** to **{today.date()}**")

results = []
for ticker, meta in tickers.items():
    if meta["region"] not in region_filter:
        continue
    if sector_filter and meta["sector"] not in sector_filter:
        continue
    try:
        df = yf.download(ticker, start=start_date, end=today, progress=False)
        if df.empty:
            continue
        start_price = df['Close'].iloc[0]
        end_price = df['Close'].iloc[-1]
        pct = round(((end_price - start_price) / start_price) * 100, 2)
        results.append({
            "Ticker": ticker,
            "Name": meta["name"],
            "Region": meta["region"],
            "Sector": meta["sector"],
            f"% Change ({timeframe})": pct
        })
    except:
        continue

df_result = pd.DataFrame(results).sort_values(by=f"% Change ({timeframe})", ascending=False)
st.dataframe(df_result)
