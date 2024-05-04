import json
import oandapyV20.endpoints.positions as positions
import oandapyV20.endpoints.transactions as transactions
from datetime import datetime
import pandas as pd
import oandapyV20
from oandapyV20.endpoints.accounts import AccountDetails
import oandapyV20.endpoints.trades as trades

import numpy as np

access_token = "3f0f1b513d44797ff63c09d9da612561-6480f119d75e63cea1e420564d12b6f1"
account_id = "101-003-28603773-001"


accountID = account_id
access_token = access_token
client = oandapyV20.API(access_token=access_token, environment="practice")


# Fetch transactions
def fetch_transactions(open_date, current_date):
    open_date = open_date.strftime('%Y-%m-%dT%H:%M:%S.000000Z')
    current_date = current_date.strftime('%Y-%m-%dT%H:%M:%S.000000Z')

    params = {
        "from": open_date,
        "to": current_date,
        "type": "ORDER_FILL"
    }
    r = transactions.TransactionList(accountID=account_id, params=params)
    data = client.request(r)

    all_transactions = []
    for page in data['pages']:
        id_range = get_from_to_values(page)
        r = transactions.TransactionIDRange(accountID=account_id, params={'from': id_range['from'], 'to': id_range['to']})
        data = client.request(r)
        all_transactions.extend(data['transactions'])

    return all_transactions

def get_from_to_values(text):
    from urllib.parse import urlparse

    # Parse the URL
    parsed_url = urlparse(text)
    query_params = parsed_url.query.split('&')

    # Extract 'from' and 'to' values
    result = {}
    for param in query_params:
        key, value = param.split('=')
        if key.lower() == 'from':
            result['from'] = int(value)
        elif key.lower() == 'to':
            result['to'] = int(value)

    # Return results or None if not found
    return result or None

# Process transactions to calculate equity
def process_transactions(transactions,capital):
    df = pd.DataFrame(transactions)
    df = df[df['type'] == 'ORDER_FILL']
    df['time'] = pd.to_datetime(df['time'])
    df['amount'] = pd.to_numeric(df['pl'], errors='coerce').fillna(0)
    df['cumulative'] = capital + df['amount'].cumsum()
    df.set_index('time', inplace=True)
    return df

# Calculate drawdowns
def calculate_drawdowns(df):
    df['peak'] = df['cumulative'].cummax()
    df['drawdown'] = df['peak'] - df['cumulative']
    df['drawdown_pct'] = (df['drawdown'] / df['peak']) * 100
    return df

def get_current_balance():
    request = AccountDetails(accountID=accountID)
    response = client.request(request)

    if response and 'account' in response:
        account_info = response['account']
        balance = float(account_info['balance'])
        return balance
        
    return None

def calculate_annualised_returns(capital, total_trading_days):
    if total_trading_days == 0:
        return 0
    
    current_balance = get_current_balance()
    annualised_returns = ( (current_balance/capital * 100 ) / int(total_trading_days) )* 252

    return annualised_returns


def fetch_balance_changes(open_date, current_date):
    open_date = open_date.strftime('%Y-%m-%dT%H:%M:%S.000000Z')
    current_date = current_date.strftime('%Y-%m-%dT%H:%M:%S.000000Z')

    params = {
        "from": open_date,
        "to": current_date,
        "type": "ORDER_FILL"
    }
    r = transactions.TransactionList(accountID=account_id, params=params)
    data = client.request(r)

    # gather transactions
    all_transactions = []
    for page in data['pages']:
        id_range = get_from_to_values(page)
        r = transactions.TransactionIDRange(accountID=account_id, params={'from': id_range['from'], 'to': id_range['to']})
        data = client.request(r)
        all_transactions.extend(data['transactions'])

    # gather daily changes
    df = pd.DataFrame(all_transactions)
    
    if not df.empty:
        # pd.to_numeric(df['accountBalance'], errors='coerce')
        df['amount'] = pd.to_numeric(df['accountBalance'], errors='coerce')
        df['pct_change'] = df['amount'].pct_change()
        df['time'] = pd.to_datetime(df['time'])
        print(df.describe())
        df.set_index('time', inplace=True)
        df = df.resample('D').last()  # end of day balance

    return df

def calculate_sharpe_ratio(df):
    # The risk-free daily rate assume 1% annual rate
    risk_free_rate = 0.01 / 365
    print(df.describe())
    print(df.head())
    
    # Calculate daily excess return
    daily_excess_return = df['pct_change'] - risk_free_rate

    # Calculate daily standard deviation
    daily_std = np.std(daily_excess_return)

    # Calculate daily Sharpe Ratio
    daily_sharpe = daily_excess_return.mean() / daily_std
    
    # Sharpe ratio
    annual_sharpe = daily_sharpe * np.sqrt(252)  # sqrt(252) annualizes the standard deviation
    
    return annual_sharpe

def fetch_closed_trades():
    r = trades.TradesList(accountID=account_id, params={"state": "CLOSED"})
    resp = client.request(r)
    return resp['trades']

def calculate_win_rate_from_trades(trades):
    if len(trades) == 0:
        return 0

    wins = sum(1 for trade in trades if float(trade['realizedPL']) > 0)
    losses = sum(1 for trade in trades if float(trade['realizedPL']) < 0)
    total_trades = wins + losses
    win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0
    return win_rate

def pnl_all_positions():
    request = positions.OpenPositions(accountID=account_id)
    response = client.request(request)
    open_positions = response.get("positions", [])
    pnl = sum([float(pos['unrealizedPL']) for pos in open_positions])
    return pnl
