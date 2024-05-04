import numpy as np
from oandapyV20 import API
import oandapyV20
import oandapyV20.endpoints.positions as positions
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.trades as trades
import oandapyV20.endpoints.pricing as pricing
from oandapyV20.endpoints.instruments import InstrumentsCandles
from datetime import date, timedelta
import pandas_ta
from pandas_ta.volatility import thermo, true_range, pdist, bbands, rvi, massi
import pandas as pd
import joblib


access_token = "3f0f1b513d44797ff63c09d9da612561-6480f119d75e63cea1e420564d12b6f1"
account_id = "101-003-28603773-001"

accountID = account_id
access_token = access_token

client = oandapyV20.API(access_token=access_token, environment="practice")

#Model Features
model_1min_features = ['DPO_20', 'SLOPE_1', 'BBB_5_2.0']
model_5min_features = ['DPO_20', 'THERMO_20_2_0.5', 'SLOPE_1', 'BBB_5_2.0', 'CFO_9', 'PDIST', 'BOP', 'BEARP_13', 'TRUERANGE_1']
model_15min_features = ['DPO_20', 'THERMO_20_2_0.5', 'CFO_9', 'TRUERANGE_1', 'PDIST', 'BBB_5_2.0', 'RVI_14', 'SLOPE_1', 'BULLP_13', 'BOP']
model_1hour_features = ['DPO_20', 'THERMO_20_2_0.5', 'TRUERANGE_1', 'SLOPE_1', 'PDIST', 'CFO_9', 'BOP', 'RVI_14', 'BBB_5_2.0', 'BBP_5_2.0', 'MASSI_9_25']

#Pairs mapping
pairs_mapping = {
    'EUR_USD': 'EURUSD=X',
    'USD_JPY': 'JPY=X',   
    'GBP_USD': 'GBPUSD=X',
    'AUD_USD': 'AUDUSD=X',
    'NZD_USD': 'NZDUSD=X',
    'USD_HKD': 'HKD=X',
    'USD_SGD': 'SGD=X',
    'USD_MXN': 'MXN=X',
    'USD_THB': 'THB=X',
    'USD_ZAR': 'ZAR=X',
}

def get_current_price(instrument):
    params = {
        "instruments": instrument
    }
    request = pricing.PricingInfo(accountID=account_id, params=params)
    response = client.request(request)

    if 'prices' in response and response['prices']:
        return float(response['prices'][0]['bids'][0]['price'])

    return None

# for 1 min
def get_top3_features(open, high, low, close):
  # top 3 features 'DPO_20', 'BBB_5_2.0, 'SLOPE_1'
  dpo_df = pandas_ta.trend.dpo(close)
  bbands_df = bbands(close)
  slope_df = pandas_ta.momentum.slope(close)

  combined = pd.concat([dpo_df, bbands_df, slope_df], axis=1)
  return combined[model_1min_features].copy()

# for 5 min
def get_top9_features(open, high, low, close):
  # top 9 features 'DPO_20', 'THERMO_20_2_0.5', 'SLOPE_1', 'BBB_5_2.0', 'CFO_9', 'PDIST', 'BOP', 'BEARP_13', 'TRUERANGE_1'
  dpo_df = pandas_ta.trend.dpo(close)
  thermo_df = thermo(high, low)
  slope_df = pandas_ta.momentum.slope(close)
  bbands_df = bbands(close)
  cfo_df = pandas_ta.momentum.cfo(close)
  pdist_df = pdist(open, high, low, close)
  bop_df = pandas_ta.momentum.bop(open, high, low, close)
  eri_df = pandas_ta.momentum.eri(high, low, close)
  truerange_df = true_range(high, low, close)

  combined = pd.concat([dpo_df, thermo_df, slope_df, bbands_df, cfo_df, bop_df, pdist_df, eri_df, truerange_df], axis=1)
  return combined[model_5min_features].copy()

# for 15 min
def get_top10_features(open, high, low, close):
    # top 10 features 'DPO_20', 'THERMO_20_2_0.5', 'CFO_9', 'TRUERANGE_1', 'PDIST', 'BBB_5_2.0', 'RVI_14', 'SLOPE_1', 'BULLP_13', 'BOP'
    dpo_df = pandas_ta.trend.dpo(close)
    thermo_df = thermo(high, low)
    cfo_df = pandas_ta.momentum.cfo(close)
    truerange_df = true_range(high, low, close)
    pdist_df = pdist(open, high, low, close)
    bbands_df = bbands(close)
    #cci_df = pandas_ta.momentum.cci(high, low, close)
    rvi_df = rvi(close, high, low)
    slope_df = pandas_ta.momentum.slope(close)
    eri_df = pandas_ta.momentum.eri(high, low, close)
    bop_df = pandas_ta.momentum.bop(open, high, low, close)

    combined = pd.concat([dpo_df, thermo_df, slope_df, cfo_df, truerange_df, bbands_df, rvi_df, pdist_df, eri_df, bop_df], axis=1)
    return combined[model_15min_features].copy()

# for 1hour
def get_top11_features(open, high, low, close):
  # top 11 features 'DPO_20', 'THERMO_20_2_0.5', 'TRUERANGE_1', 'SLOPE_1', 'PDIST', 'CFO_9', 'BOP', 'RVI_14', 'BBB_5_2.0', 'BBP_5_2.0', 'MASSI_9_25'
  dpo_df = pandas_ta.trend.dpo(close)
  thermo_df = thermo(high, low)
  truerange_df = true_range(high, low, close)
  slope_df = pandas_ta.momentum.slope(close)
  pdist_df = pdist(open, high, low, close)
  cfo_df = pandas_ta.momentum.cfo(close)
  bop_df = pandas_ta.momentum.bop(open, high, low, close)
  rvi_df = rvi(close, high, low)
  bbands_df = bbands(close)
  #kurtosis_df = pandas_ta.statistics.kurtosis(close)
  massi_df = massi(high, low)
  #er_df = pandas_ta.momentum.er(close)
  #cci_df = pandas_ta.momentum.cci(high, low, close)

  combined = pd.concat([dpo_df, thermo_df, slope_df, massi_df, cfo_df, truerange_df, bbands_df, rvi_df, pdist_df, bop_df], axis=1)
  return combined[model_1hour_features].copy()

def fetch_candlestick_data(instrument_name, granularity, lookback_count):
    # Initialize the Oanda API client
    api = API(access_token=access_token, environment="practice")
    #UTC time zone
    # Define the parameters for the candlestick data request
    params = {
        'count': lookback_count,
        'granularity': granularity,
        'price': 'MBA',  #mid, bid, ask
    }

    # Request the candlestick data from Oanda API
    candles_request = InstrumentsCandles(instrument=instrument_name, params=params)
    response = api.request(candles_request)

    price_data = []
    for entry in response['candles']:
        price_entry = {
            'time': entry['time'],
            'volume': entry['volume'],
            'bid_close': float(entry['bid']['c']),
            'ask_close': float(entry['ask']['c']),
            'm_open': float(entry['mid']['o']),
            'm_high': float(entry['mid']['h']),
            'm_low': float(entry['mid']['l']),
            'm_close': float(entry['mid']['c'])
        }
        price_data.append(price_entry)
    price_df = pd.DataFrame(price_data)
    
    # Extract the close prices from the response
    # close_prices = [float(candle['mid']['c']) for candle in response['candles']]
    # bid_prices = [float(candle['bid']['c']) for candle in response['candles']]
    # ask_prices = [float(candle['ask']['c']) for candle in response['candles']]
    # #volume = [float(candle['volume']['c']) for candle in response['candles']]

    return price_df

def data_preparation(model_type, instrument,lookback_count):
    if model_type == "models_1mins":
        model_strategy = joblib.load("models_1mins.joblib")
        model_1min_features = ['DPO_20', 'SLOPE_1', 'BBB_5_2.0']
        granularity = "M1"
        price_df = fetch_candlestick_data(instrument, granularity, lookback_count)
        top_df3 = get_top3_features(price_df["m_open"], price_df["m_high"], price_df["m_low"], price_df["m_close"])

        price_df = pd.concat([price_df, top_df3], axis=1)
        model_data = price_df[model_1min_features]
        # make prediction for the next period price direction
        # get the currency pair's mode
        model = model_strategy[pairs_mapping[instrument]]
        # save the predicted y direction
        #   1 is positive => buy t+1, 0 is not positive => sell t+1
        y_pred = model.predict(model_data)
        price_df["prediction_on_next_close"] = [1 if x > 0 else -1 for x in y_pred]

    elif model_type == "models_5mins":
        
        model_strategy = joblib.load("models_5mins.joblib")
        model_5min_features = ['DPO_20', 'THERMO_20_2_0.5', 'SLOPE_1', 'BBB_5_2.0', 'CFO_9', 'PDIST', 'BOP', 'BEARP_13', 'TRUERANGE_1']
        granularity = 'M5'        
        price_df = fetch_candlestick_data(instrument, granularity, lookback_count)
        top_df = get_top9_features(price_df["m_open"], price_df["m_high"], price_df["m_low"], price_df["m_close"])
        price_df = pd.concat([price_df, top_df], axis=1)
        model_data = price_df[model_5min_features]
        # make prediction for the next period price direction
        # get the currency pair's mode
        model = model_strategy[pairs_mapping[instrument]]
        # save the predicted y direction
        #   1 is positive => buy t+1, 0 is not positive => sell t+1
        y_pred = model.predict(model_data)
        price_df["prediction_on_next_close"] = [1 if x > 0 else -1 for x in y_pred]

    elif model_type == "models_15mins":
        
        model_strategy = joblib.load("models_15mins.joblib")
        model_15min_features = ['DPO_20', 'THERMO_20_2_0.5', 'CFO_9', 'TRUERANGE_1', 'PDIST', 'BBB_5_2.0', 'RVI_14', 'SLOPE_1', 'BULLP_13', 'BOP']   
        granularity = 'M15'      

        price_df = fetch_candlestick_data(instrument, granularity, lookback_count)
        top_df = get_top10_features(price_df["m_open"], price_df["m_high"], price_df["m_low"], price_df["m_close"])
        price_df = pd.concat([price_df, top_df], axis=1)
        model_data = price_df[model_15min_features]
        # make prediction for the next period price direction
        # get the currency pair's mode
        model = model_strategy[pairs_mapping[instrument]]
        # save the predicted y direction
        #   1 is positive => buy t+1, 0 is not positive => sell t+1
        y_pred = model.predict(model_data)
        price_df["prediction_on_next_close"] = [1 if x > 0 else -1 for x in y_pred]
    
    elif model_type == "models_1hour":
        model_strategy = joblib.load("models_1hour.joblib")        
        model_1hour_features = ['DPO_20', 'THERMO_20_2_0.5', 'TRUERANGE_1', 'SLOPE_1', 'PDIST', 'CFO_9', 'BOP', 'RVI_14', 'BBB_5_2.0', 'BBP_5_2.0', 'MASSI_9_25']
        granularity = 'H1'     

        price_df = fetch_candlestick_data(instrument, granularity, lookback_count)
        top_df = get_top11_features(price_df["m_open"], price_df["m_high"], price_df["m_low"], price_df["m_close"])
        price_df = pd.concat([price_df, top_df], axis=1)
        model_data = price_df[model_15min_features]
        # make prediction for the next period price direction
        # get the currency pair's mode
        model = model_strategy[pairs_mapping[instrument]]
        # save the predicted y direction
        #   1 is positive => buy t+1, 0 is not positive => sell t+1
        y_pred = model.predict(model_data)
        price_df["prediction_on_next_close"] = [1 if x > 0 else -1 for x in y_pred]

    else:
        model_strategy = joblib.load("models_15mins.joblib")
        model_15min_features = ['DPO_20', 'THERMO_20_2_0.5', 'CFO_9', 'TRUERANGE_1', 'PDIST', 'BBB_5_2.0', 'RVI_14', 'SLOPE_1', 'BULLP_13', 'BOP']   
        granularity = 'M15'      

        price_df = fetch_candlestick_data(instrument, granularity, lookback_count)
        top_df = get_top10_features(price_df["m_open"], price_df["m_high"], price_df["m_low"], price_df["m_close"])
        price_df = pd.concat([price_df, top_df], axis=1)
        model_data = price_df[model_15min_features]
        # make prediction for the next period price direction
        # get the currency pair's mode
        model = model_strategy[pairs_mapping[instrument]]
        # save the predicted y direction
        #   1 is positive => buy t+1, 0 is not positive => sell t+1
        y_pred = model.predict(model_data)
        price_df["prediction_on_next_close"] = [1 if x > 0 else -1 for x in y_pred]

    return price_df
   