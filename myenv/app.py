import vectorbt as vbt
import yfinance as yf

btc_price = vbt.YFData.download(
    "BTC-USD",
    missing_index='drop').get("Close")

print(btc_price)
