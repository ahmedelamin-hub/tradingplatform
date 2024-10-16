import sys
import os
import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from strategies import ema_strategy
from utils.plot_utils import plot_backtest_results
sys.path.append(os.path.join(os.path.dirname(__file__), 'alpaca'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'my_binance'))
from alpaca import run_live_strategy_alpaca, backtest_alpaca, fetch_alpaca_balance, get_open_positions_alpaca, close_position_alpaca, close_all_positions_alpaca, fetch_alpaca_pending_orders, cancel_order_alpaca
from my_binance.my_binance import run_live_strategy_binance, backtest_binance, fetch_binance_balance, get_open_positions_binance, close_position_binance, close_all_positions_binance

# Streamlit setup
st.set_page_config(page_title='Vision Trading', layout='wide', page_icon="📈", initial_sidebar_state="expanded")

# Display balances at the top of the page
st.title("Vision Trading Dashboard")
balance_alpaca = st.empty()
balance_binance = st.empty()

# Display balances function
def display_balances():
    alpaca_balance = fetch_alpaca_balance()
    binance_balance = fetch_binance_balance()

    if binance_balance is None:
        balance_binance.metric("Binance Balance (USDT)", "Error fetching balance")
    else:
        balance_binance.metric("Binance Balance (USDT)", f"${binance_balance:,.2f}")
    
    balance_alpaca.metric("Alpaca Balance", f"${alpaca_balance:,.2f}")

# Sidebar for exchange selection
st.sidebar.title("Select Exchange")
exchange = st.sidebar.selectbox("Choose Exchange", ["Alpaca", "Binance Futures"])

# Input fields
symbol = st.sidebar.text_input("Symbol", value="AAPL" if exchange == "Alpaca" else "BTCUSDT")
dollar_amount = st.sidebar.number_input("Amount to Allocate ($)", value=100)

# Alpaca trading options
if exchange == "Alpaca":
    st.write("Alpaca exchange selected")
    trade_action = st.sidebar.radio("Action", ["buy", "sell short"])

    if st.sidebar.button("Run Alpaca Live Strategy"):
        positions = run_live_strategy_alpaca(symbol, trade_action, dollar_amount)
        if positions is not None:
            st.write(f"Alpaca live strategy executed for {trade_action} on {symbol}")
        else:
            st.error(f"Error executing Alpaca live strategy for {trade_action} on {symbol}")

    # Backtesting settings
    short_ema_period = st.sidebar.number_input("Short EMA Period", value=10, min_value=1)
    long_ema_period = st.sidebar.number_input("Long EMA Period", value=20, min_value=1)
    start_date = st.sidebar.date_input("Start Date", value=pd.to_datetime("2021-01-01"))
    end_date = st.sidebar.date_input("End Date", value=pd.to_datetime("2022-01-01"))

    # Convert to timezone-aware datetime
    start_date_tz = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=pytz.UTC)
    end_date_tz = datetime.combine(end_date, datetime.min.time()).replace(tzinfo=pytz.UTC)

    if st.sidebar.button("Backtest Alpaca"):
        st.write("Starting Alpaca backtest")
        portfolio = backtest_alpaca(symbol, start_date_tz, end_date_tz, short_ema_period, long_ema_period, dollar_amount)
        if portfolio is None:
            st.error("No data returned for backtest. Please check the date range and symbol.")
        else:
            plot_backtest_results(portfolio)

    # Display open positions for Alpaca
    open_positions = get_open_positions_alpaca()
    if open_positions is not None:
        st.write("### Open Positions (Alpaca)")
        st.table(open_positions)

        # Close specific positions
        for index, row in open_positions.iterrows():
            if st.button(f"Close {row['Symbol']} position"):
                close_position_alpaca(row['Symbol'])

        if st.button("Close All Alpaca Positions"):
            close_all_positions_alpaca()
    else:
        st.write("No open positions found.")

    # Display pending orders for Alpaca
    open_orders = fetch_alpaca_pending_orders()
    if open_orders is not None:
        st.write("### Pending Orders (Alpaca)")
        st.table(open_orders)

        for index, row in open_orders.iterrows():
            if st.button(f"Cancel Order {row['Order ID']}"):
                cancel_order_alpaca(row['Order ID'])

# Binance trading options
elif exchange == "Binance Futures":
    st.write("Binance Futures exchange selected")
    margin = st.sidebar.number_input("Leverage (Margin)", value=5, min_value=1, max_value=125)
    trade_action = st.sidebar.radio("Trade Action", ["buy", "sell"])

    if st.sidebar.button("Run Binance Live Strategy"):
        run_live_strategy_binance(symbol, margin, dollar_amount, trade_action)
        st.write(f"Binance live strategy executed for {trade_action} on {symbol}")

    # Backtesting settings
    short_ema_period = st.sidebar.number_input("Short EMA Period", value=10, min_value=1)
    long_ema_period = st.sidebar.number_input("Long EMA Period", value=20, min_value=1)
    start_date = st.sidebar.date_input("Start Date", value=pd.to_datetime("2021-01-01"))
    end_date = st.sidebar.date_input("End Date", value=pd.to_datetime("2022-01-01"))

    if st.sidebar.button("Backtest Binance"):
        st.write("Starting Binance backtest")
        portfolio = backtest_binance(symbol, start_date, end_date, short_ema_period, long_ema_period, dollar_amount)
        if portfolio is None:
            st.error("No data returned for backtest. Please check the date range and symbol.")
        else:
            plot_backtest_results(portfolio)

    # Display open positions for Binance
    open_positions = get_open_positions_binance()
    if open_positions is not None:
        st.write("### Open Positions (Binance)")
        st.table(open_positions)

        for index, row in open_positions.iterrows():
            if st.button(f"Close {row['Symbol']} position"):
                close_position_binance(row['Symbol'], abs(float(row['Size'])), 'sell' if float(row['Size']) > 0 else 'buy')

        if st.button("Close All Binance Positions"):
            close_all_positions_binance()
    else:
        st.write("No open positions found.")

# Display balances
display_balances()
