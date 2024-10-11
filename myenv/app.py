# app.py
import vectorbt as vbt
import yfinance as yf
from strategies.rsi import run_rsi_strategy

# Function to fetch BTC price
def btc_price():
    return vbt.YFData.download("BTC-USD", missing_index='drop').get("Close")

# Main entry point to run the app
if __name__ == "__main__":
    # Fetch BTC price and pass it to the RSI strategy
    price_data = btc_price()
    total_return = run_rsi_strategy(price_data)
    print(f"Total Return: {total_return}")
