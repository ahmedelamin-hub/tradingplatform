import plotly.graph_objs as go
import streamlit as st

# Function to plot backtest results across various tabs
def plot_backtest_results(portfolio):
    """
    Display the results of a backtest in four different tabs:
    - Backtesting Stats: Displays key performance metrics.
    - List of Trades: Displays all trades made during the backtest.
    - Equity Curve: Shows the portfolio value over time.
    - Drawdown: Shows the drawdown of the portfolio over time.
    
    Args:
        portfolio (object): Portfolio object from VectorBT backtest.
    """
    # Create tabs for displaying different aspects of the backtest
    tab1, tab2, tab3, tab4 = st.tabs(["Backtesting Stats", "List of Trades", "Equity Curve", "Drawdown"])

    # Tab 1: Display backtesting statistics
    with tab1:
        # Get the portfolio stats and display in a table
        stats_df = portfolio.stats(silence_warnings=True)  # Suppress warnings for stats
        st.dataframe(stats_df)

    # Tab 2: Display a list of trades
    with tab2:
        # Display all trades in a readable format
        st.dataframe(portfolio.trades.records_readable)

    # Tab 3: Plot the equity curve (portfolio value over time)
    with tab3:
        # Create a line chart for portfolio value
        st.plotly_chart(go.Figure(
            data=[go.Scatter(x=portfolio.value().index, y=portfolio.value(), mode='lines')]
        ))

    # Tab 4: Plot the drawdown (percentage drop from peak portfolio value)
    with tab4:
        # Create a line chart for drawdown, filling the area below the curve
        st.plotly_chart(go.Figure(
            data=[go.Scatter(x=portfolio.drawdown().index, 
                             y=portfolio.drawdown() * 100, 
                             mode='lines', 
                             fill='tozeroy')]
        ))
