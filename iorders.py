import streamlit as st
import pandas as pd
import alpaca_trade_api as tradeapi

# Alpaca API Keys
APCA_API_BASE_URL = "https://paper-api.alpaca.markets"
APCA_API_KEY_ID = "PK77AYZXRSTU37E27EK3"
APCA_API_SECRET_KEY = "8DC7dFVtJwRNJacM6seYyvsrYinftFtpJgxv1Fa1"

# Initialize Alpaca client
alpaca = tradeapi.REST(APCA_API_KEY_ID, APCA_API_SECRET_KEY, APCA_API_BASE_URL, api_version='v2')

# Function to fetch Alpaca account balance and display it
def fetch_and_display_balance():
    try:
        account = alpaca.get_account()
        cash_balance = float(account.cash)
        st.metric("Available Cash (USD)", f"${cash_balance:,.2f}")
        return cash_balance
    except Exception as e:
        st.error(f"Error fetching account balance: {e}")
        return 0

# Function to fetch Alpaca live account positions and display in a table
def fetch_and_display_positions():
    try:
        positions = alpaca.list_positions()
        open_positions = []
        for position in positions:
            open_positions.append({
                'Asset': position.symbol,
                'Price': f"${float(position.current_price):.2f}",
                'Qty': float(position.qty),
                'Market Value': f"${float(position.market_value):.2f}",
                'Total P/L ($)': f"${float(position.unrealized_pl):.4f}"
            })

        if open_positions:
            df = pd.DataFrame(open_positions)
            st.table(df)
        else:
            st.info("No open positions found.")
    except Exception as e:
        st.error(f"Error fetching open positions from Alpaca: {e}")

