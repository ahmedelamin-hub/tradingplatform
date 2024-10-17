import alpaca_trade_api as tradeapi
import vectorbt as vbt
import pandas as pd

# Alpaca API setup (keys will be passed as arguments)
def initialize_alpaca_client(api_key, api_secret):
    return tradeapi.REST(api_key, api_secret, base_url="https://paper-api.alpaca.markets", api_version='v2')

# Fetch Alpaca balance and PnL
def fetch_alpaca_balance(client):
    try:
        account = client.get_account()
        balance = float(account.cash)
        pnl = float(account.unrealized_pl) if hasattr(account, 'unrealized_pl') else 0  # Default PnL to 0 if not available
        return balance, pnl
    except Exception as e:
        print(f"Error fetching Alpaca balance: {e}")
        return None, None  # Return None for both if there's an error

# Alpaca live strategy
def run_live_strategy_alpaca(client, symbol, action, dollar_amount):
    try:
        side = 'buy' if action == 'buy' else 'sell'
        order = client.submit_order(
            symbol=symbol,
            qty=dollar_amount,  # Calculate this based on the price if needed
            side=side,
            type='market',
            time_in_force='day'  # Ensure fractional orders use DAY
        )
        print(f"{action.capitalize()} order placed for {symbol}")
        return get_open_positions_alpaca(client)

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

# Get open positions for Alpaca with PnL
def get_open_positions_alpaca(client):
    try:
        positions = client.list_positions()
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

# Close specific position in Alpaca with correct fractional handling
def close_position_alpaca(client, symbol):
    try:
        position = client.get_position(symbol)
        qty = position.qty

        if float(qty) <= 0:
            print(f"Invalid quantity {qty} for {symbol}.")
            return

        # Convert qty to string to handle fractional shares properly and use DAY for fractional orders
        side = 'sell' if float(qty) > 0 else 'buy'
        client.submit_order(
            symbol=symbol,
            qty=str(float(qty)),  # Ensure qty is a string and supports fractional shares
            side=side,
            type='market',
            time_in_force='day'  # Fractional orders must use 'day'
        )
        print(f"Closed position for {symbol}")
    except Exception as e:
        print(f"Error closing position for {symbol}: {e}")

# Close all positions in Alpaca
def close_all_positions_alpaca(client):
    try:
        positions = client.list_positions()
        for position in positions:
            close_position_alpaca(client, position.symbol)
        print("All positions closed successfully.")
    except Exception as e:
        print(f"Error closing all positions: {e}")

# Fetch pending orders from Alpaca
def fetch_alpaca_pending_orders(client):
    try:
        orders = client.list_orders(status='open')
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
def cancel_order_alpaca(client, order_id):
    try:
        client.cancel_order(order_id)
        print(f"Order {order_id} cancelled successfully.")
    except Exception as e:
        print(f"Error cancelling order {order_id}: {e}")