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
from alpaca import initialize_alpaca_client, run_live_strategy_alpaca, backtest_alpaca, get_open_positions_alpaca, close_position_alpaca, close_all_positions_alpaca, fetch_alpaca_pending_orders, cancel_order_alpaca, fetch_alpaca_balance
from my_binance.my_binance import initialize_binance_client, run_live_strategy_binance, backtest_binance, get_open_positions_binance, close_position_binance, close_all_positions_binance, fetch_binance_balance

# Streamlit setup
st.set_page_config(page_title='Vision Trading', layout='wide', page_icon="📈", initial_sidebar_state="expanded")

# Initialize session state for API keys and refresh counter
if 'alpaca_api_key' not in st.session_state:
    st.session_state['alpaca_api_key'] = ''
    st.session_state['alpaca_secret_key'] = ''
if 'binance_api_key' not in st.session_state:
    st.session_state['binance_api_key'] = ''
    st.session_state['binance_secret_key'] = ''
if 'refresh_count' not in st.session_state:
    st.session_state['refresh_count'] = 0  # Initialize refresh counter

# Display balances at the top of the page
st.title("Vision Trading Dashboard")
balance_alpaca = st.empty()  # Placeholder for Alpaca balance
balance_binance = st.empty()  # Placeholder for Binance balance

# Sidebar for exchange selection
st.sidebar.title("Select Exchange")
exchange = st.sidebar.selectbox("Choose Exchange", ["Alpaca", "Binance Futures"])

# Input fields for API keys
st.sidebar.write("Enter your API keys")

# Persist API keys in session state
if exchange == "Alpaca":
    st.session_state['alpaca_api_key'] = st.sidebar.text_input("Alpaca API Key", value=st.session_state['alpaca_api_key'], type="password")
    st.session_state['alpaca_secret_key'] = st.sidebar.text_input("Alpaca Secret Key", value=st.session_state['alpaca_secret_key'], type="password")

if exchange == "Binance Futures":
    st.session_state['binance_api_key'] = st.sidebar.text_input("Binance API Key", value=st.session_state['binance_api_key'], type="password")
    st.session_state['binance_secret_key'] = st.sidebar.text_input("Binance Secret Key", value=st.session_state['binance_secret_key'], type="password")

# Input fields for symbol and amount
symbol = st.sidebar.text_input("Symbol", value="AAPL" if exchange == "Alpaca" else "BTCUSDT")
dollar_amount = st.sidebar.number_input("Amount to Allocate ($)", value=100)

# Refresh Button
if st.sidebar.button("Refresh Positions"):
    st.session_state['refresh_count'] += 1  # Increment refresh counter to trigger re-run

# Display balances function with PnL
def display_balances():
    if exchange == "Alpaca":
        if st.session_state['alpaca_api_key'] and st.session_state['alpaca_secret_key']:
            # Initialize Alpaca client with user-provided API keys
            client = initialize_alpaca_client(st.session_state['alpaca_api_key'], st.session_state['alpaca_secret_key'])
            balance, pnl = fetch_alpaca_balance(client)
            if balance is not None and pnl is not None:
                balance_alpaca.metric("Alpaca Balance", f"${balance:,.2f}")
                st.metric("Alpaca PnL", f"${pnl:,.2f}")
            else:
                st.write("Error fetching Alpaca balance or PnL")
        else:
            st.write("No Alpaca API linked. Live trading features are disabled.")
    
    if exchange == "Binance Futures":
        if st.session_state['binance_api_key'] and st.session_state['binance_secret_key']:
            # Initialize Binance client with user-provided API keys
            client = initialize_binance_client(st.session_state['binance_api_key'], st.session_state['binance_secret_key'])
            balance_binance.metric("Binance Balance (USDT)", f"${fetch_binance_balance(client):,.2f}")
        else:
            st.write("No Binance API linked. Live trading features are disabled.")

# Binance closing logic update
def close_position_binance(client, symbol, size, side):
    try:
        if float(size) > 0:  # Long position
            side = 'sell'
        elif float(size) < 0:  # Short position
            side = 'buy'

        client.futures_create_order(
            symbol=symbol,
            side=side,
            type='MARKET',
            quantity=abs(float(size))  # Ensure we're using absolute size
        )
        st.success(f"Closed position for {symbol}")
    except Exception as e:
        st.error(f"Error closing position for {symbol}: {e}")

# Alpaca trading options
if exchange == "Alpaca":
    st.write("Alpaca exchange selected")
    
    if st.session_state['alpaca_api_key'] and st.session_state['alpaca_secret_key']:
        # Initialize Alpaca client
        client = initialize_alpaca_client(st.session_state['alpaca_api_key'], st.session_state['alpaca_secret_key'])
        trade_action = st.sidebar.radio("Action", ["buy", "sell short"])

        if st.sidebar.button("Run Alpaca Live Strategy"):
            positions = run_live_strategy_alpaca(client, symbol, trade_action, dollar_amount)
            if positions is not None:
                st.write(f"Alpaca live strategy executed for {trade_action} on {symbol}")
            else:
                st.error(f"Error executing Alpaca live strategy for {trade_action} on {symbol}")
    else:
        st.write("Live trading is disabled since no Alpaca API keys are linked.")

    # Backtesting settings for Alpaca (available without API keys)
    short_ema_period = st.sidebar.number_input("Short EMA Period", value=10, min_value=1)
    long_ema_period = st.sidebar.number_input("Long EMA Period", value=20, min_value=1)
    start_date = st.sidebar.date_input("Start Date", value=pd.to_datetime("2021-01-01"))
    end_date = st.sidebar.date_input("End Date", value=pd.to_datetime("2022-01-01"))

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
    if st.session_state['alpaca_api_key'] and st.session_state['alpaca_secret_key']:
        open_positions = get_open_positions_alpaca(client)
        if open_positions is not None:
            st.write("### Open Positions (Alpaca)")
            st.table(open_positions)

            for index, row in open_positions.iterrows():
                if st.button(f"Close {row['Symbol']} position"):
                    # Close specific position for Alpaca (with correct fractional handling)
                    close_position_alpaca(client, row['Symbol'])

            if st.button("Close All Alpaca Positions"):
                close_all_positions_alpaca(client)

        # Fetch unfilled orders from Alpaca
        st.write("### Pending Orders (Alpaca)")
        pending_orders = fetch_alpaca_pending_orders(client)
        if pending_orders is not None:
            st.table(pending_orders)

            for index, row in pending_orders.iterrows():
                if st.button(f"Cancel Order {row['Order ID']}"):
                    cancel_order_alpaca(client, row['Order ID'])

        else:
            st.write("No pending orders found.")
    else:
        st.write("No API linked. No open positions.")

# Binance trading options
elif exchange == "Binance Futures":
    st.write("Binance Futures exchange selected")
    
    if st.session_state['binance_api_key'] and st.session_state['binance_secret_key']:
        # Initialize Binance client
        client = initialize_binance_client(st.session_state['binance_api_key'], st.session_state['binance_secret_key'])
        margin = st.sidebar.number_input("Leverage (Margin)", value=5, min_value=1, max_value=125)
        trade_action = st.sidebar.radio("Trade Action", ["buy", "sell"])

        # Ensure that the EMA strategy places a short position (not just closing long)
        if st.sidebar.button("Run Binance Live Strategy"):
            if trade_action == "sell":
                # Place a short position instead of closing the long one
                run_live_strategy_binance(client, symbol, margin, dollar_amount, "short")
            else:
                run_live_strategy_binance(client, symbol, margin, dollar_amount, trade_action)
            st.write(f"Binance live strategy executed for {trade_action} on {symbol}")
    else:
        st.write("Live trading is disabled since no Binance API keys are linked.")

    # Backtesting settings for Binance (available without API keys)
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
    if st.session_state['binance_api_key'] and st.session_state['binance_secret_key']:
        open_positions = get_open_positions_binance(client)
        if open_positions is not None:
            st.write("### Open Positions (Binance)")
            st.table(open_positions)

            for index, row in open_positions.iterrows():
                if st.button(f"Close {row['Symbol']} position"):
                    side = 'sell' if float(row['Size']) > 0 else 'buy'  # Determine side based on position size
                    close_position_binance(client, row['Symbol'], abs(float(row['Size'])), side)

            if st.button("Close All Binance Positions"):
                close_all_positions_binance(client)
        else:
            st.write("No open positions found.")
    else:
        st.write("No API linked. No open positions.")

# Display balances
display_balances()
