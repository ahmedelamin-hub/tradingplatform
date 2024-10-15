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

# Function to fetch Alpaca live account positions and display with close buttons
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
            st.write("### Open Positions")
            st.table(df)

            # Add buttons to close specific asset positions
            for position in positions:
                symbol = position.symbol
                qty = abs(float(position.qty))
                if st.button(f"Close Position: {symbol}", key=f"{symbol}_close"):
                    close_position(symbol, qty)
        else:
            st.info("No open positions found.")
    except Exception as e:
        st.error(f"Error fetching open positions from Alpaca: {e}")

# Function to close specific asset position
def close_position(symbol, qty):
    try:
        side = 'sell' if qty > 0 else 'buy'
        alpaca.submit_order(
            symbol=symbol,
            qty=abs(qty),
            side=side,
            type='market',
            time_in_force='day'  # Fix for fractional shares
        )
        st.success(f"Closed position for {symbol}")
    except Exception as e:
        st.error(f"Error closing position for {symbol}: {e}")

# Function to fetch Alpaca open orders and display with cancel buttons
def fetch_and_display_open_orders():
    try:
        orders = alpaca.list_orders(status='open', limit=100)
        if orders:
            open_orders = []
            for order in orders:
                open_orders.append({
                    'Asset': order.symbol,
                    'Qty': order.qty,
                    'Side': order.side,
                    'Type': order.type,
                    'Status': order.status,
                    'Submitted At': order.submitted_at,
                })
            df = pd.DataFrame(open_orders)
            st.write("### Open Orders")
            st.table(df)

            # Add buttons to cancel specific orders (use unique order ID as key)
            for order in orders:
                symbol = order.symbol
                if st.button(f"Cancel Order: {symbol}", key=f"{symbol}_{order.id}_cancel"):
                    cancel_order(order.id)

            # Add a button to cancel all open orders
            if st.button("Cancel All Open Orders"):
                cancel_all_orders()

        else:
            st.info("No open orders found.")
    except Exception as e:
        st.error(f"Error fetching open orders from Alpaca: {e}")

# Function to cancel a specific open order
def cancel_order(order_id):
    try:
        alpaca.cancel_order(order_id)
        st.success("Order cancelled successfully.")
    except Exception as e:
        st.error(f"Error cancelling order: {e}")

# Function to cancel all open orders
def cancel_all_orders():
    try:
        orders = alpaca.list_orders(status='open', limit=100)
        for order in orders:
            alpaca.cancel_order(order.id)
        st.success("All open orders cancelled!")
    except Exception as e:
        st.error(f"Error cancelling all orders: {e}")

# Function to close all positions
def close_all_positions():
    try:
        positions = alpaca.list_positions()
        for position in positions:
            qty = abs(float(position.qty))
            close_position(position.symbol, qty)
        st.success("All positions closed!")
    except Exception as e:
        st.error(f"Error closing positions: {e}")

# EMA Strategy implementation
def run_ema_strategy(symbol, short_ema_period, long_ema_period, dollar_amount, side):
    try:
        # Fetch the latest trade price to calculate how many shares to trade
        latest_trade = alpaca.get_latest_trade(symbol)
        price = latest_trade.price
        qty = dollar_amount / price  # Calculate quantity based on dollar amount

        # Execute the trade based on EMA strategy logic
        order = alpaca.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type='market',
            time_in_force='day'
        )
        st.success(f"EMA {side.capitalize()} order placed for {symbol}. Amount: ${dollar_amount:.2f}, Shares: {qty:.4f}")
        return order
    except Exception as e:
        st.error(f"Error running EMA strategy for {symbol}: {e}")
        return None

# Function to buy or sell using Alpaca
def place_order(symbol, dollar_amount, side):
    try:
        # Fetch the latest trade price to calculate how many shares to buy/sell
        latest_trade = alpaca.get_latest_trade(symbol)
        price = latest_trade.price
        qty = dollar_amount / price  # Calculate quantity based on dollar amount
        order = alpaca.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type='market',
            time_in_force='day'  # Ensure this is a day order for fractional shares
        )
        st.success(f"{side.capitalize()} order placed for {symbol}. Amount: ${dollar_amount:.2f}, Shares: {qty:.4f}")
        return order
    except Exception as e:
        st.error(f"Error placing {side} order for {symbol}: {e}")
        return None

# Streamlit interface
st.set_page_config(page_title='Vision Trading (Alpaca)', layout='wide', page_icon="📈", initial_sidebar_state="expanded")

# Sidebar for inputs
st.sidebar.title("Vision Trading")

# Fetch and display the current available cash balance and daily change
available_cash = fetch_and_display_balance()

# Trading Inputs
st.sidebar.header("Alpaca Trading and EMA Strategy")
symbol = st.sidebar.text_input("Enter Alpaca symbol (e.g., 'AAPL')", value="AAPL")
dollar_amount = st.sidebar.number_input("Amount in Dollars ($)", value=100)
trade_action = st.sidebar.radio("Trade Action", ["buy", "sell"])

# EMA Strategy Inputs
short_ema_period = st.sidebar.number_input("Short EMA Period", value=10, min_value=1)
long_ema_period = st.sidebar.number_input("Long EMA Period", value=20, min_value=1)
use_ema = st.sidebar.checkbox("Use EMA Strategy", value=False)

# Button to place orders or run EMA strategy
if st.sidebar.button("Execute Trade"):
    if use_ema:
        run_ema_strategy(symbol, short_ema_period, long_ema_period, dollar_amount, trade_action)
    else:
        place_order(symbol, dollar_amount, trade_action)

# Button to close all positions
st.sidebar.button("Close All Positions", on_click=close_all_positions)

# Main area to display current open positions
st.title("Alpaca Trading Dashboard")
fetch_and_display_positions()

# Section for open orders with individual cancel buttons and the ability to cancel all
fetch_and_display_open_orders()

# Manual refresh option using a button (removing experimental_rerun)
if st.button("Refresh Data"):
    st.info("Refresh the page manually for updates.")
