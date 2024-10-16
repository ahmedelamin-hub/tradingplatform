import plotly.graph_objs as go
import streamlit as st

def plot_backtest_results(portfolio):
    tab1, tab2, tab3, tab4 = st.tabs(["Backtesting Stats", "List of Trades", "Equity Curve", "Drawdown"])

    with tab1:
        stats_df = portfolio.stats(silence_warnings=True)  # Removed 'freq'
        st.dataframe(stats_df)

    with tab2:
        st.dataframe(portfolio.trades.records_readable)

    with tab3:
        st.plotly_chart(go.Figure(data=[go.Scatter(x=portfolio.value().index, y=portfolio.value(), mode='lines')]))

    with tab4:
        st.plotly_chart(go.Figure(data=[go.Scatter(x=portfolio.drawdown().index, y=portfolio.drawdown() * 100, mode='lines', fill='tozeroy')]))
