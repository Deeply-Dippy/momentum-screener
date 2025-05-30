import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import numpy as np

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
        # Download data for single ticker
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=today)
        
        # Check if data exists
        if df.empty:
            errors.append(f"{ticker}: No data available")
            continue
            
        if len(df) < 2:
            errors.append(f"{ticker}: Insufficient data points")
            continue
        
        # Get close prices - handle both single and multi-index columns
        if 'Close' in df.columns:
            close_prices = df['Close']
        elif ('Close', ticker) in df.columns:
            close_prices = df[('Close', ticker)]
        else:
            # Try to find any close column
            close_cols = [col for col in df.columns if 'Close' in str(col)]
            if close_cols:
                close_prices = df[close_cols[0]]
            else:
                errors.append(f"{ticker}: No Close price column found")
                continue
        
        # Remove any NaN values and get first and last prices
        close_prices = close_prices.dropna()
        
        if len(close_prices) < 2:
            errors.append(f"{ticker}: Insufficient valid price data")
            continue
        
        start_price = float(close_prices.iloc[0])
        end_price = float(close_prices.iloc[-1])
        
        # Validate prices
        if start_price <= 0 or end_price <= 0:
            errors.append(f"{ticker}: Invalid price values")
            continue
        
        # Calculate percentage change
        pct_change = ((end_price - start_price) / start_price) * 100
        pct_change = round(pct_change, 2)
        
        results.append({
            "Ticker": ticker,
            "Name": meta["name"],
            "Region": meta["region"],
            "Sector": meta["sector"],
            "Start_Price": round(start_price, 2),
            "End_Price": round(end_price, 2),
            "Percent_Change": pct_change
        })
        
    except Exception as e:
        errors.append(f"{ticker}: Error - {str(e)}")
        continue

# Display results
if results:
    try:
        # Create DataFrame
        df_result = pd.DataFrame(results)
        
        # Ensure all numeric columns are properly typed
        numeric_cols = ["Start_Price", "End_Price", "Percent_Change"]
        for col in numeric_cols:
            df_result[col] = pd.to_numeric(df_result[col], errors='coerce')
        
        # Remove any rows with NaN values in critical columns
        df_result = df_result.dropna(subset=["Percent_Change"])
        
        if not df_result.empty:
            # Sort by percentage change (descending) - use explicit method
            df_result = df_result.sort_values(by="Percent_Change", ascending=False, na_position='last')
            
            # Create display DataFrame with renamed columns
            display_df = df_result.copy()
            display_df = display_df.rename(columns={
                "Start_Price": f"Start Price",
                "End_Price": f"End Price", 
                "Percent_Change": f"% Change ({timeframe})"
            })
            
            # Reset index for clean display
            display_df = display_df.reset_index(drop=True)
            
            st.dataframe(display_df, use_container_width=True)
            
            # Show summary stats
            col1, col2, col3 = st.columns(3)
            
            with col1:
                top_performer = df_result.iloc[0]
                st.metric(
                    label="🏆 Top Performer",
                    value=f"{top_performer['Name']} ({top_performer['Ticker']})",
                    delta=f"{top_performer['Percent_Change']}%"
                )
            
            with col2:
                avg_change = df_result['Percent_Change'].mean()
                st.metric(
                    label="📊 Average Change",
                    value=f"{avg_change:.2f}%"
                )
            
            with col3:
                total_stocks = len(df_result)
                positive_stocks = len(df_result[df_result['Percent_Change'] > 0])
                st.metric(
                    label="📈 Positive Performers",
                    value=f"{positive_stocks}/{total_stocks}",
                    delta=f"{(positive_stocks/total_stocks*100):.1f}% positive"
                )
        else:
            st.warning("No valid data available after processing.")
    
    except Exception as e:
        st.error(f"Error processing results: {str(e)}")
        st.write("Raw results for debugging:")
        st.write(results)
else:
    st.warning("No data available for the selected criteria.")

# Show errors if any
if errors:
    with st.expander("⚠️ Data Fetch Issues", expanded=False):
        for error in errors:
            st.text(error)
