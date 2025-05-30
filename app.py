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
errors = []

for ticker, meta in tickers.items():
    if meta["region"] not in region_filter:
        continue
    if sector_filter and meta["sector"] not in sector_filter:
        continue
    
    try:
        # Download data with error handling
        df = yf.download(ticker, start=start_date, end=today, progress=False)
        
        if df.empty:
            errors.append(f"{ticker}: No data available")
            continue
            
        if len(df) < 2:
            errors.append(f"{ticker}: Insufficient data points")
            continue
        
        # Get first and last valid prices
        start_price = df['Close'].iloc[0]
        end_price = df['Close'].iloc[-1]
        
        # Validate prices
        if pd.isna(start_price) or pd.isna(end_price):
            errors.append(f"{ticker}: Invalid price data")
            continue
            
        if start_price <= 0:
            errors.append(f"{ticker}: Invalid start price")
            continue
        
        # Calculate percentage change
        pct_change = ((end_price - start_price) / start_price) * 100
        
        # Round to 2 decimal places
        pct_change = round(float(pct_change), 2)
        
        results.append({
            "Ticker": ticker,
            "Name": meta["name"],
            "Region": meta["region"],
            "Sector": meta["sector"],
            "Percent_Change": pct_change  # Using fixed column name
        })
        
    except Exception as e:
        errors.append(f"{ticker}: {str(e)}")
        continue

# Display results
if results:
    # Create DataFrame
    df_result = pd.DataFrame(results)
    
    # Ensure numeric column
    df_result["Percent_Change"] = pd.to_numeric(df_result["Percent_Change"], errors='coerce')
    
    # Remove any NaN values
    df_result = df_result.dropna(subset=["Percent_Change"])
    
    if not df_result.empty:
        # Sort by percentage change (descending)
        df_result = df_result.sort_values("Percent_Change", ascending=False)
        
        # Rename column for display
        df_result = df_result.rename(columns={"Percent_Change": f"% Change ({timeframe})"})
        
        # Reset index for clean display
        df_result = df_result.reset_index(drop=True)
        
        st.dataframe(df_result, use_container_width=True)
        
        # Show top performer
        if len(df_result) > 0:
            top_performer = df_result.iloc[0]
            st.success(f"🏆 Top Performer: **{top_performer['Name']} ({top_performer['Ticker']})** with {top_performer[f'% Change ({timeframe})']}%")
    else:
        st.warning("No valid data available after filtering.")
else:
    st.warning("No data available for the selected criteria.")

# Show errors if any (in expander to not clutter the main view)
if errors:
    with st.expander("⚠️ Data Fetch Issues", expanded=False):
        for error in errors:
            st.text(error)
