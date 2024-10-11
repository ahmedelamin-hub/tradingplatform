# strategies/rsi.py
import vectorbt as vbt

def run_rsi_strategy(btc_price):
    # Run the RSI strategy
    rsi = vbt.RSI.run(btc_price, window=14)

    # Define entry and exit signals based on RSI
    entries = rsi.rsi_crossed_below(20)
    exits = rsi.rsi_crossed_above(80)

    # Create the portfolio from entry and exit signals
    pf = vbt.Portfolio.from_signals(btc_price, entries, exits)

    # Plot the portfolio's performance
    pf.plot().show()

    # Return the total return of the portfolio
    return pf.total_return()
