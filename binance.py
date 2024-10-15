import streamlit as st
import vectorbt as vbt
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from datetime import datetime
import pytz
from binance.client import Client
from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_MARKET
import time

# API Key for Binance Futures Testnet
API_KEY = "70d56a2c1a1f5fc16aa0077b1eb40dbb1f87d8451afb7483b9292f79c6363f18"
API_SECRET = "aa050e6b4f9753234aa445fdf2fe87ec3fc8549ad217d61feef417411fe28959"

# Binance Client for Testnet
client = Client(API_KEY, API_SECRET, testnet=True)

# Synchronize with Binance server time
server_time = client.futures_time()
client.timestamp_offset = server_time['serverTime'] - int(time.time() * 1000)

# Convert date to datetime with timezone
def convert_to_timezone_aware(date_obj):
    return datetime.combine(date_obj, datetime.min.time()).replace(tzinfo=pytz.UTC)

# Function to fetch live account balance
def get_balance():
    try:
        balance = client.futures_account_balance()
        for asset in balance:
            if asset['asset'] == 'USDT':
                return float(asset['balance'])
    except Exception as e:
        st.error(f"Error fetching balance: {e}")
        return None

# Function to fetch detailed open positions with relevant fields
def get_open_positions():
    try:
        positions = client.futures_position_information()
        account_info = client.futures_account()  # Fetching account details for margin information
        for asset in account_info['assets']:
            if asset['asset'] == 'USDT':
                margin_balance = float(asset['marginBalance'])

        open_positions = []
        for pos in positions:
            if float(pos['positionAmt']) != 0:  # Only include positions with a non-zero size
                entry_price = float(pos['entryPrice'])
                mark_price = float(pos['markPrice'])
                pnl = (mark_price - entry_price) * float(pos['positionAmt'])
                roi = (pnl / margin_balance) * 100 if margin_balance > 0 else 0

                open_positions.append({
                    'Symbol': pos['symbol'],
                    'Size': pos['positionAmt'],
                    'Entry Price': entry_price,
                    'Break Even Price': pos['entryPrice'],  # Adjust this based on fees if necessary
                    'Mark Price': mark_price,
                    'Liq. Price': float(pos['liquidationPrice']),
                    'Margin Type': pos['marginType'],  # Keep marginType as string (e.g., 'cross' or 'isolated')
                    'Margin': margin_balance,  # You may want to adjust based on the position size
                    'PNL(ROI %)': f"{pnl:.2f} USDT ({roi:.2f}%)",
                    'Reverse': '',  # Add a button for reversing position (if needed)
                    'TP/SL for Position': '',  # Display this when you implement TP/SL settings
                    'TP/SL': '',  # Display current TP/SL values (if applicable)
                })
        return open_positions
    except Exception as e:
        st.error(f"Error fetching positions: {e}")
        return []

# Function to close an individual position
def close_position(symbol, size, side):
    try:
        client.futures_create_order(symbol=symbol, side=side, type=ORDER_TYPE_MARKET, quantity=size)
        st.success(f"Closed position for {symbol}")
    except Exception as e:
        st.error(f"Error closing position for {symbol}: {e}")

# Function to close all open positions
def close_all_positions():
    try:
        positions = get_open_positions()
        for pos in positions:
            symbol = pos['Symbol']
            qty = abs(float(pos['Size']))
            side = SIDE_SELL if float(pos['Size']) > 0 else SIDE_BUY
            client.futures_create_order(symbol=symbol, side=side, type=ORDER_TYPE_MARKET, quantity=qty)
        st.success("All positions closed!")
    except Exception as e:
        st.error(f"Error closing positions: {e}")

# Function for Binance Live Trading
def run_live_strategy_binance(symbol, margin, allocated_margin, short_ema_period, long_ema_period, side):
    st.write(f"Running Live Strategy on Binance Testnet for {symbol} with {margin}x leverage...")

    # Change leverage
    try:
        client.futures_change_leverage(symbol=symbol, leverage=int(margin))
        st.write(f"Leverage set to {margin}x for {symbol}")
    except Exception as e:
        st.error(f"Error setting leverage: {e}")

    # Fetch live data
    klines = client.futures_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_1MINUTE, limit=1000)
    data = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 
                                         'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 
                                         'taker_buy_quote_asset_volume', 'ignore'])

    data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
    data.set_index('timestamp', inplace=True)
    data['close'] = data['close'].astype(float)

    # Calculate EMAs
    short_ema = data['close'].ewm(span=short_ema_period, adjust=False).mean()
    long_ema = data['close'].ewm(span=long_ema_period, adjust=False).mean()

    # Determine position size based on allocated margin
    latest_price = data['close'].iloc[-1]
    position_size = allocated_margin * margin / latest_price

    # Place buy or sell order
    try:
        if side == 'buy':
            order = client.futures_create_order(
                symbol=symbol,
                side=SIDE_BUY,
                type=ORDER_TYPE_MARKET,
                quantity=round(position_size, 3),
                marginType="ISOLATED"
            )
        else:
            order = client.futures_create_order(
                symbol=symbol,
                side=SIDE_SELL,
                type=ORDER_TYPE_MARKET,
                quantity=round(position_size, 3),
                marginType="ISOLATED"
            )
        st.success(f"{side.capitalize()} order placed: {order}")
        return order['orderId']
    except Exception as e:
        st.error(f"Error placing order: {e}")
        return None

# Streamlit interface
st.set_page_config(page_title='Vision', layout='wide', page_icon="📈", initial_sidebar_state="expanded")

# Inject CSS for the custom color theme and the dashboard button
st.markdown(
    """
    <style>
    .css-18e3th9 {
        background-color: #344767;
    }
    .css-1d391kg {
        color: white;
    }
    .button {
        background-color: #4CAF50;
        border: none;
        color: white;
        padding: 10px 24px;
        text-align: center;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        width: 100%;
    }
    .button:hover {
        background-color: #45a049;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Sidebar for inputs
st.sidebar.title("Vision Trading")

# Professional Dashboard Button
st.sidebar.markdown(
    """
    <a href="http://localhost:3000/dashboard" target="_self">
    <button class="button">Go to Dashboard</button>
    </a>
    """, unsafe_allow_html=True
)

st.sidebar.header("Choose Exchange")
source = st.sidebar.selectbox("Choose Exchange", ["Alpaca", "Binance Futures"])

if source == "Alpaca":
    symbol = st.sidebar.text_input("Enter the Alpaca symbol (e.g., 'AAPL')", value="HDFCBANK.NS")
    start_date = st.sidebar.date_input("Start Date", value=pd.to_datetime("2010-01-01"), max_value=pd.to_datetime("2024-01-01"))
    end_date = st.sidebar.date_input("End Date", value=pd.to_datetime("2024-01-01"), max_value=pd.to_datetime("2024-12-31"))
    size = st.sidebar.number_input("Position Size", value=100)  # Input for position size for Alpaca backtesting
    initial_equity = st.sidebar.number_input("Initial Equity", value=100000)  # Only for Alpaca
    
    # Parameters only for Alpaca (Yahoo finance under the hood)
    size_type = st.sidebar.selectbox("Size Type", ["amount", "value", "percent"], index=2)
    fees = st.sidebar.number_input("Fees (as %)", value=0.12, format="%.4f")
    direction = st.sidebar.selectbox("Direction", ["longonly", "shortonly", "both"], index=0)

elif source == "Binance Futures":
    symbol = st.sidebar.selectbox("Select Cryptocurrency Pair (Binance Futures)", ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT"])
    margin = st.sidebar.number_input("Select Leverage (Margin)", value=5, min_value=1, max_value=125)
    allocated_margin = st.sidebar.number_input("Amount to Allocate ($)", value=1000)  # Only for Binance Futures

    # Trade Action: Buy or Sell
    trade_action = st.sidebar.radio("Trade Action", ["buy", "sell"])

# Strategies Section
with st.sidebar.expander("Strategies"):
    st.header("EMA Strategy Parameters")
    short_ema_period = st.sidebar.number_input("Short EMA Period", value=10, min_value=1)
    long_ema_period = st.sidebar.number_input("Long EMA Period", value=20, min_value=1)

# Buttons
backtest_clicked = st.sidebar.button("Backtest")
simulate_clicked = st.sidebar.button("Simulate")
live_clicked = st.sidebar.button("Run Live Strategy")

# Function to fetch historical data (for Alpaca placeholder, under Yahoo Finance)
@st.cache_data
def load_data(symbol, start, end):
    return vbt.YFData.download(symbol, start=start, end=end).get('Close')

# Main area for results
if backtest_clicked or simulate_clicked or live_clicked:
    # Alpaca Backtesting (Yahoo Finance as a placeholder)
    if backtest_clicked and source == "Alpaca":
        start_date_tz = convert_to_timezone_aware(start_date)
        end_date_tz = convert_to_timezone_aware(end_date)

        # Fetch data for backtesting (Yahoo Finance)
        data = load_data(symbol, start_date_tz, end_date_tz)

        if data.empty:
            st.error("No data found for the selected symbol and date range.")
        else:
            # Calculate EMAs and signals
            short_ema = vbt.MA.run(data, short_ema_period, short_name='fast', ewm=True)
            long_ema = vbt.MA.run(data, long_ema_period, short_name='slow', ewm=True)
            entries = short_ema.ma_crossed_above(long_ema)
            exits = short_ema.ma_crossed_below(long_ema)

            if entries.sum() == 0 or exits.sum() == 0:
                st.warning("No trade signals generated. Adjust the strategy parameters.")
            else:
                size_value = float(size) if size_type != 'percent' else float(size) / 100.0
                portfolio = vbt.Portfolio.from_signals(
                    data, entries, exits, direction=direction, size=size_value,
                    size_type=size_type, fees=fees / 100, init_cash=initial_equity, freq='1D'
                )

                # Check if trades were made during backtest
                if portfolio.trades.records.shape[0] == 0:
                    st.error("No trades were made during the backtest.")
                else:
                    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Backtesting Stats", "List of Trades", "Equity Curve", "Drawdown", "Portfolio Plot"])

                    with tab1:
                        st.markdown("**Backtesting Stats:**")
                        stats_df = pd.DataFrame(portfolio.stats(), columns=['Value'])
                        st.dataframe(stats_df, height=800)

                    with tab2:
                        st.markdown("**List of Trades:**")
                        trades_df = portfolio.trades.records_readable
                        st.dataframe(trades_df.round(2), width=800, height=600)

                    equity_data = portfolio.value()
                    drawdown_data = portfolio.drawdown() * 100

                    with tab3:
                        equity_trace = go.Scatter(x=equity_data.index, y=equity_data, mode='lines', name='Equity')
                        equity_fig = go.Figure(data=[equity_trace])
                        st.plotly_chart(equity_fig)

                    with tab4:
                        drawdown_trace = go.Scatter(x=drawdown_data.index, y=drawdown_data, mode='lines', name='Drawdown', fill='tozeroy')
                        drawdown_fig = go.Figure(data=[drawdown_trace])
                        st.plotly_chart(drawdown_fig)

                    with tab5:
                        st.markdown("**Portfolio Plot:**")
                        st.plotly_chart(portfolio.plot())

    # Binance Futures Simulation
    if simulate_clicked and source == "Binance Futures":
        simulate_binance()

    # Binance Futures Live Trading
    if live_clicked and source == "Binance Futures":
        order_id = run_live_strategy_binance(symbol, margin, allocated_margin, short_ema_period, long_ema_period, trade_action)

# Show balance and other Binance features only when Binance Futures is selected
if source == "Binance Futures":
    st.subheader("Running Bots")

    # Fetch and display balance
    balance = get_balance()
    if balance is not None:
        st.metric("Available Balance (USDT)", f"${balance:.2f}")

    # Fetch the positions data
    positions = get_open_positions()
    if positions:
        df = pd.DataFrame(positions)

        # Show the relevant columns neatly
        df = df[['Symbol', 'Size', 'Entry Price', 'Break Even Price', 'Mark Price', 
                 'Liq. Price', 'Margin Type', 'Margin', 'PNL(ROI %)', 'Reverse', 
                 'TP/SL for Position', 'TP/SL']]

        # Display in a user-friendly table
        st.table(df)

        # Buttons to close each position
        for index, row in df.iterrows():
            symbol = row['Symbol']
            size = abs(float(row['Size']))
            close_position_button = st.button(f"Close {symbol} position", key=f"{symbol}_{index}")
            if close_position_button:
                side = SIDE_SELL if float(row['Size']) > 0 else SIDE_BUY
                close_position(symbol, size, side)

    # Button to close all positions
    st.button("Close All Positions", on_click=close_all_positions)
