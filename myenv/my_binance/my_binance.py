from binance.client import Client
import pandas as pd
from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_MARKET
import streamlit as st
import time

# Binance Futures API setup
BINANCE_API_KEY = "70d56a2c1a1f5fc16aa0077b1eb40dbb1f87d8451afb7483b9292f79c6363f18"
BINANCE_API_SECRET = "aa050e6b4f9753234aa445fdf2fe87ec3fc8549ad217d61feef417411fe28959"
client = Client(BINANCE_API_KEY, BINANCE_API_SECRET, testnet=True)

# Synchronize with Binance server time
try:
    server_time = client.futures_time()
    client.timestamp_offset = server_time['serverTime'] - int(time.time() * 1000)
except Exception as e:
    st.error(f"Error syncing with Binance server time: {e}")

# Fetch Binance balance
def fetch_binance_balance():
    try:
        balance = client.futures_account_balance()
        for asset in balance:
            if asset['asset'] == 'USDT':
                return float(asset['balance'])
    except Exception as e:
        st.error(f"Error fetching Binance balance: {e}")
        return None

# Binance live strategy
def run_live_strategy_binance(symbol, margin, allocated_margin, side):
    try:
        # Change leverage
        client.futures_change_leverage(symbol=symbol, leverage=int(margin))
        print(f"Leverage set to {margin}x for {symbol}")
        
        # Fetch the latest price
        latest_price_info = client.futures_mark_price(symbol=symbol)
        latest_price = float(latest_price_info['markPrice'])
        print(f"Latest Price: {latest_price}")

        # Calculate position size based on allocated margin and price
        position_size = allocated_margin / latest_price
        print(f"Calculated Position Size: {position_size}")

        # Ensure the notional value of the position is at least $100
        notional_value = position_size * latest_price
        if notional_value < 100:
            st.error(f"Error: Position size too small. Notional value must be at least $100. Current notional: {notional_value:.2f}")
            return None

        # Check symbol precision (this might differ between pairs)
        precision = 3  # Adjust precision based on symbol requirements
        
        # Place a buy or sell order
        side_enum = SIDE_BUY if side == 'buy' else SIDE_SELL
        order = client.futures_create_order(
            symbol=symbol,
            side=side_enum,
            type=ORDER_TYPE_MARKET,
            quantity=round(position_size, precision),  # Adjust quantity for precision
            marginType="ISOLATED"  # Ensure isolated margin mode is used
        )
        st.success(f"{side.capitalize()} order placed: {symbol}, Size: {position_size}")
        return order

    except Exception as e:
        st.error(f"Error placing {side} order: {e}")
        return None

# Backtest Binance function
def backtest_binance(symbol, start_date, end_date, short_ema_period, long_ema_period, allocated_margin):
    try:
        # Fetch historical data (using Binance API)
        klines = client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1MINUTE, start_date, end_date)
        if not klines:
            st.error("No data received from Binance")
            return None

        # Convert the data into a DataFrame
        data = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 
                                             'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 
                                             'taker_buy_quote_asset_volume', 'ignore'])
        data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
        data.set_index('timestamp', inplace=True)
        data['close'] = data['close'].astype(float)

        # Calculate EMAs
        short_ema = data['close'].ewm(span=short_ema_period).mean()
        long_ema = data['close'].ewm(span=long_ema_period).mean()

        # Create buy/sell signals based on EMA crossovers
        entries = short_ema > long_ema
        exits = short_ema < long_ema

        # Ensure that the frequency is set (1 minute in this case)
        freq = '1T'  # 1 minute
        data = data.asfreq(freq)

        # Simulate portfolio using VectorBT
        portfolio = vbt.Portfolio.from_signals(data['close'], entries, exits, init_cash=allocated_margin, freq=freq)
        return portfolio

    except Exception as e:
        st.error(f"Error during Binance backtest: {e}")
        return None

# Get open positions
def get_open_positions_binance():
    try:
        positions = client.futures_position_information()
        open_positions = []
        for pos in positions:
            if float(pos['positionAmt']) != 0:  # Only include non-zero positions
                pnl = pos.get('unrealizedProfit', 0)  # Use 0 if 'unrealizedProfit' is missing
                open_positions.append({
                    'Symbol': pos['symbol'],
                    'Size': pos['positionAmt'],
                    'Entry Price': pos['entryPrice'],
                    'Mark Price': pos['markPrice'],
                    'PNL': pnl
                })
        if not open_positions:
            return None  # No open positions found
        return pd.DataFrame(open_positions)

    except Exception as e:
        st.error(f"Error fetching open positions: {e}")
        return None

# Close a specific Binance position
def close_position_binance(symbol, size, side):
    try:
        client.futures_create_order(symbol=symbol, side=side, type=ORDER_TYPE_MARKET, quantity=size)
        st.success(f"Closed position for {symbol}")
    except Exception as e:
        st.error(f"Error closing position for {symbol}: {e}")

# Close all Binance positions
def close_all_positions_binance():
    try:
        positions = get_open_positions_binance()
        if positions is not None:
            for index, row in positions.iterrows():
                symbol = row['Symbol']
                size = abs(float(row['Size']))
                side = SIDE_SELL if float(row['Size']) > 0 else SIDE_BUY
                close_position_binance(symbol, size, side)
            st.success("All Binance positions closed!")
    except Exception as e:
        st.error(f"Error closing all positions: {e}")
