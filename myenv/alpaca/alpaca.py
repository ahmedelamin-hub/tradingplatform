import alpaca_trade_api as tradeapi
import vectorbt as vbt
import pandas as pd

# Alpaca API setup
APCA_API_BASE_URL = "https://paper-api.alpaca.markets"
APCA_API_KEY_ID = "PK77AYZXRSTU37E27EK3"
APCA_API_SECRET_KEY = "8DC7dFVtJwRNJacM6seYyvsrYinftFtpJgxv1Fa1"
alpaca = tradeapi.REST(APCA_API_KEY_ID, APCA_API_SECRET_KEY, APCA_API_BASE_URL, api_version='v2')

# Fetch Alpaca balance
def fetch_alpaca_balance():
    try:
        account = alpaca.get_account()
        return float(account.cash)
    except Exception as e:
        print(f"Error fetching Alpaca balance: {e}")
        return None

# Alpaca live strategy
def run_live_strategy_alpaca(symbol, action, dollar_amount):
    try:
        side = 'buy' if action == 'buy' else 'sell'
        order = alpaca.submit_order(
            symbol=symbol,
            qty=dollar_amount,  # Calculate this based on the price if needed
            side=side,
            type='market',
            time_in_force='day'
        )
        print(f"{action.capitalize()} order placed for {symbol}")

        # Fetch current positions
        return get_open_positions_alpaca()

    except Exception as e:
        print(f"Error executing Alpaca strategy: {e}")
        return None

# Backtest Alpaca
def backtest_alpaca(symbol, start_date, end_date, short_ema_period, long_ema_period, allocated_margin):
    try:
        data = vbt.YFData.download(symbol, start=start_date, end=end_date).get('Close')
        short_ema = data.ewm(span=short_ema_period).mean()
        long_ema = data.ewm(span=long_ema_period).mean()

        entries = short_ema > long_ema
        exits = short_ema < long_ema

        portfolio = vbt.Portfolio.from_signals(data, entries, exits, init_cash=allocated_margin)
        return portfolio
    except Exception as e:
        print(f"Error during Alpaca backtest: {e}")
        return None

# Get open positions for Alpaca
def get_open_positions_alpaca():
    try:
        positions = alpaca.list_positions()
        open_positions = []
        for pos in positions:
            open_positions.append({
                'Symbol': pos.symbol,
                'Qty': pos.qty,
                'Entry Price': pos.avg_entry_price,
                'Current Price': pos.current_price,
                'Market Value': pos.market_value,
                'Unrealized PnL': pos.unrealized_pl
            })
        if not open_positions:
            return None
        return pd.DataFrame(open_positions)

    except Exception as e:
        print(f"Error fetching open positions: {e}")
        return None

# Close specific position in Alpaca
def close_position_alpaca(symbol):
    try:
        position = alpaca.get_position(symbol)
        qty = position.qty
        side = 'sell' if int(qty) > 0 else 'buy'
        alpaca.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type='market',
            time_in_force='gtc'
        )
        print(f"Closed position for {symbol}")
    except Exception as e:
        print(f"Error closing position for {symbol}: {e}")

# Close all positions in Alpaca
def close_all_positions_alpaca():
    try:
        positions = alpaca.list_positions()
        for position in positions:
            close_position_alpaca(position.symbol)
        print("All positions closed successfully.")
    except Exception as e:
        print(f"Error closing all positions: {e}")

# Fetch pending orders from Alpaca
def fetch_alpaca_pending_orders():
    try:
        orders = alpaca.list_orders(status='open')
        if orders:
            pending_orders = []
            for order in orders:
                pending_orders.append({
                    "Order ID": order.id,
                    "Symbol": order.symbol,
                    "Qty": order.qty,
                    "Side": order.side,
                    "Type": order.type,
                    "Status": order.status
                })
            return pd.DataFrame(pending_orders)
        return None
    except Exception as e:
        print(f"Error fetching pending orders: {e}")
        return None

# Cancel pending order in Alpaca
def cancel_order_alpaca(order_id):
    try:
        alpaca.cancel_order(order_id)
        print(f"Order {order_id} cancelled successfully.")
    except Exception as e:
        print(f"Error cancelling order {order_id}: {e}")
