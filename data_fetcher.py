import numpy as np
import pandas as pd
from oandapyV20 import API
#API processes requests that can be created fro the endpoints
from oandapyV20.endpoints.instruments import InstrumentsCandles

access_token = "fc55828bad637666f39996dd32b6d527-e32e012b7ea4947bd3a6a62a2de6c049"
# account_id = "101-003-28582948-001"

# accountID = account_id
access_token = access_token

def fetch_data(instrument_name, granularity='S5', lookback_count=100):
    # Initialize the Oanda API client
    api = API(access_token=access_token, environment="practice")

    # Define the parameters for the candlestick data request
    params = {
        'count': lookback_count,
        'granularity': granularity,
        'price': 'M',  # Midpoint candlestick prices
    }

    # Request the candlestick data from Oanda API
    candles_request = InstrumentsCandles(instrument=instrument_name, params=params)
    response = api.request(candles_request)

    # Extract the close prices from the response
    # close_prices = [float(candle['mid']['c']) for candle in response['candles']]

    df = to_yfinance(response)

    return df


def to_yfinance(response):
    candles = []
    for candle in response['candles']:
        # Extract open (o), high (h), low (l), and close (c) prices from the 'mid' dictionary
        candles.append({'Date': candle['time'],
                        'Open': candle['mid']['o'],
                        'High': candle['mid']['h'],
                        'Low': candle['mid']['l'],
                        'Close': candle['mid']['c'],
                        'Volume': candle['volume']})
    
    # Create the DataFrame
    df = pd.DataFrame(candles)

    # Convert 'time' column to datetime format: '2024-01-01'
    df['Date'] = pd.to_datetime(df['Date'])#.dt.strftime('%Y-%m-%d')
    df.set_index('Date', inplace=True)
    df = df.astype({'Open': np.float64, 'High': np.float64, 'Low': np.float64, 'Close': np.float64, 'Volume': np.int64})

    return df