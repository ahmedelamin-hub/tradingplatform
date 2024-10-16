import pandas as pd

def ema_strategy(data: pd.DataFrame, short_period: int, long_period: int):
    """
    Calculate short and long EMAs, and determine buy/sell signals.
    
    Args:
        data (pd.DataFrame): DataFrame containing price data with a 'close' column.
        short_period (int): The period for the short-term EMA.
        long_period (int): The period for the long-term EMA.
    
    Returns:
        pd.Series: Short EMA, long EMA, buy signals, sell signals
    """
    # Calculate the short and long EMAs
    short_ema = data['close'].ewm(span=short_period, adjust=False).mean()
    long_ema = data['close'].ewm(span=long_period, adjust=False).mean()

    # Determine buy/sell signals based on EMA crossovers
    buy_signals = (short_ema > long_ema)  # Buy when the short EMA crosses above the long EMA
    sell_signals = (short_ema < long_ema)  # Sell when the short EMA crosses below the long EMA

    return short_ema, long_ema, buy_signals, sell_signals
