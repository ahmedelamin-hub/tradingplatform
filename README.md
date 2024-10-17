This is a tradinplatform app that i created for my final Alx  project, it allows you to connect to binancefutures testnet and Alpaca testnet. It runs an  EMA strategy that you could link directly to your live accounts. 

How to Run the App
Prerequisites:
Python 3.7 or higher installed on your system.
You should have valid API keys for both Alpaca and Binance (testnet for Binance Futures).
Basic familiarity with setting up and running Streamlit applications.

1. Clone the Repository
If you have the project in a repository, clone it to your local machine:

bash
Copy code:
git clone https://github.com/ahmedelamin-hub/tradingplatform.git

go to project dir: cd tradingplatform

2. Install Dependencies
Make sure to install all required Python packages. You can do this by running:

bash
Copy code:
pip install -r requirements.txt

3. Add Your API Keys
You can input your Alpaca and Binance API keys directly through the app UI when prompted. No need to hardcode the API keys in the code.

4. Run the App
To launch the Streamlit app, run the following command from the project directory:

bash
Copy code:
streamlit run main.py
This will start the app, and it will be available in your web browser at the address shown in the terminal (usually http://localhost:8501).

5. Features of the App
Dashboard: The main dashboard displays your balances, open positions, and lets you manage your live trading strategies and backtesting for both Alpaca and Binance Futures.

Alpaca:

View your balance and PnL.
Run live strategies for buying/selling stocks.
Backtest using EMA strategies.
View open positions and pending orders.
Close individual positions or all positions.
Binance Futures:

View your USDT balance.
Run live trading strategies with margin and leverage.
Backtest using EMA strategies.
View open positions and close individual or all positions.

6. API Keys
You will need API keys from:
Alpaca 
Binance Futures Testnet
Ensure your API keys are entered correctly when prompted in the app.

7. Troubleshooting
If you encounter any issues, ensure all dependencies are correctly installed.
If balances or positions aren't displaying, double-check that your API keys are correct and that the exchanges are not experiencing downtime.
Use the terminal to view detailed logs in case of errors.

8. Done by AhmedElamin, ahmedelamin42@gmail.com
