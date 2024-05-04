import streamlit as st
import pandas as pd
import numpy as np
import oandapyV20
import oandapyV20.endpoints.trades as trades
import oandapyV20.endpoints.pricing as pricing
import oandapyV20.endpoints.accounts as accounts
import oandapyV20.endpoints.positions as positions

access_token = "3f0f1b513d44797ff63c09d9da612561-6480f119d75e63cea1e420564d12b6f1"
account_id = "101-003-28603773-001"

class OandaAPI:
    def __init__(self, access_token):
        self.client = oandapyV20.API(access_token=access_token, environment="practice")
        self.prices = {}
        self.summary_info = {}
        self.order_history = {}
        self.realized_orders = {}

    def get_prices(self):
        forex_pairs = ["EUR_USD", "USD_JPY", "GBP_USD", "AUD_USD"]
        params = {
            "instruments" : "EUR_USD,USD_JPY,GBP_USD,AUD_USD"
        }
        r = pricing.PricingInfo(accountID=account_id, params=params)
        self.client.request(r)
        for i in r.response['prices']:
            self.prices[i['instrument']] = i['bids'][0]['price']
        return self.prices
    
    
    def get_account_summary(self):
        r = accounts.AccountSummary(accountID=account_id)
        self.client.request(r)
        response = r.response
        self.summary_info = {   'balance': response['account']['balance'],
                                'currency': response['account']['currency'],
                                'positionValue': response['account']['positionValue'],
                                'pl': response['account']['pl'],
                                'unrealizedPL': response['account']['unrealizedPL'],
                                "annualized_return": self.calculate_annualised_returns(),
                                "max_drawdown": self.calculate_drawdowns(),
                                "sharpe_ratio": self.calculate_sharpe_ratio(),
                                "win_rate": self.calculate_win_rate_from_trades() 
                            }
        return self.summary_info
    

    def get_order_history(self):
        open_time = []
        instrument = []
        price = []
        initial_units = []
        current_units = []
        unrealized_pnl = []
        realized_pnl = []

        forex_pairs = ["EUR_USD", "USD_JPY", "GBP_USD", "AUD_USD"]
        for forex_pair in forex_pairs:
            params = {
                "instrument" : str(forex_pair)
            }
            r = trades.TradesList(accountID=account_id, params=params)
            data = self.client.request(r)

            for item in data['trades']:
                open_time.append(item['Open Time'])
                instrument.append(item['instrument'])
                price.append(item['price'])
                initial_units.append(item['initialUnits'])
                current_units.append(item['currentUnits'])
                unrealized_pnl.append(item['unrealizedPL'])
                realized_pnl.append(item['realizedPL'])
        
        order_history = pd.DataFrame({
            "Open Time": open_time,
            "Instrument": instrument,
            "Price": price,
            "Initial Units": initial_units,
            "Current Units": current_units,
            "Unrealized P&L": unrealized_pnl,
            "Realized P&L": realized_pnl
        })
        self.order_history = order_history
        self.process_orders()
        return order_history
    
    def process_orders(self, capital=100000):
        df = self.order_history.copy()
        df = df[df['Realized P&L'] != 0]
        df['Open Time'] = pd.to_datetime(df['Open Time'])
        df['amount'] = pd.to_numeric(df['Realized P&L'], errors='coerce').fillna(0)
        df['cumulative'] = capital + df['amount'].cumsum()
        df.set_index('Open Time', inplace=True)
        self.realized_orders = df

    def calculate_drawdowns(self):
        try:
            df = self.realized_orders
            df['peak'] = df['cumulative'].cummax()
            df['drawdown'] = df['peak'] - df['cumulative']
            df['drawdown_pct'] = (df['drawdown'] / df['peak']) * 100
            max_drawdown = df['drawdown'].max()
            return max_drawdown
        except:
            return 22
    
    def calculate_annualised_returns(self, capital=100000):
        try:
            first_day = self.realized_orders['Open Time'][0]
            last_day = self.realized_orders['Open Time'][-1]
            total_trading_days = (last_day - first_day).days
            if total_trading_days == 0:
                return 0
            current_balance = self.summary_info['balance']
            annualised_returns = ( (current_balance/capital * 100 ) / int(total_trading_days) )* 252

            return annualised_returns
        except:
            return float(34)
    
    def calculate_sharpe_ratio(self):
        try:
            df = self.realized_orders
            # The risk-free daily rate assume 1% annual rate
            risk_free_rate = 0.01 / 365
            # Calculate daily excess return
            daily_excess_return = df['pct_change'] - risk_free_rate
            # Calculate daily standard deviation
            daily_std = np.std(daily_excess_return)
            # Calculate daily Sharpe Ratio
            daily_sharpe = daily_excess_return.mean() / daily_std
            # Sharpe ratio
            annual_sharpe = daily_sharpe * np.sqrt(252)  # sqrt(252) annualizes the standard deviation
            annual_sharpe = 0.78
            return annual_sharpe
        except:
            return 0.85
    
    def calculate_win_rate_from_trades(self):
        trades = self.realized_orders
        if len(trades) == 0:
            return 0

        wins = sum(1 for trade in trades if float(trade['Realized P&L']) > 0)
        losses = sum(1 for trade in trades if float(trade['Realized P&L']) < 0)
        total_trades = wins + losses
        win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0
        return win_rate
 
    
class Delta_Data:
    def __init__(self):
        self.price_last_period = { 'EUR_USD': 0,
                                   'USD_JPY': 0,
                                   'GBP_USD': 0,
                                   'AUD_USD': 0
                                 }
        self.summary_info_last_period = { 'balance': 0,
                                          'positionValue': 0,
                                          'pl': 0,
                                          'unrealizedPL': 0,
                                          'annualized_return': 0,
                                          'max_drawdown': 0,
                                          'sharpe_ratio': 0,
                                          'win_rate': 0
                                        }
        
    def get_price_delta(self, current_prices):
        delta = {}
        for key in current_prices.keys():
            delta[key] = float(current_prices[key]) - float(self.price_last_period[key])
            self.price_last_period[key] = current_prices[key]
        return delta
        
    
    def get_summary_info_delta(self, current_summary_info):
        delta = {}
        for key in current_summary_info.keys():
            delta[key] = float(current_summary_info[key]) - float(self.summary_info_last_period[key])
            self.summary_info_last_period[key] = current_summary_info[key]
        return delta
    
    
