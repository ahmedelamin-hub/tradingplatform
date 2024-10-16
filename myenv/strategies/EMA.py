import streamlit as st
import pandas as pd
import alpaca_trade_api as tradeapi

# Alpaca API Keys
APCA_API_BASE_URL = "https://paper-api.alpaca.markets"
APCA_API_KEY_ID = "PK77AYZXRSTU37E27EK3"
APCA_API_SECRET_KEY = "8DC7dFVtJwRNJacM6seYyvsrYinftFtpJgxv1Fa1"

# Initialize Alpaca client
alpaca = tradeapi.REST(APCA_API_KEY_ID, APCA_API_SECRET_KEY, APCA_API_BASE_URL, api_version='v2')

# Function to fetch Alpaca account balance and display it with daily change
def fetch_and_display_balance():
    try:
        account = alpaca.get_account()
        cash_balance = float(account.cash)
        equity = float(account.equity)  # Current equity
        last_equity = float(account.last_equity)  # Previous day's equity
        daily_change = equity - last_equity  # Calculate the daily change
        daily_change_pct = (daily_change / last_equity) * 100 if last_equity != 0 else 0  # Daily change percentage

        st.sidebar.metric(
            "Available Cash (USD)",
            f"${cash_balance:,.2f}",
            f"Daily Change: {daily_change_pct:.2f}% (${daily_change:,.2f})"
        )
        return cash_balance
    except Exception as e:
        st.error(f"Error fetching account balance: {e}")
        return 0