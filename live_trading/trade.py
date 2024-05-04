from returns import calculate_annualised_returns, fetch_transactions, process_transactions, calculate_drawdowns, fetch_balance_changes,calculate_sharpe_ratio, fetch_closed_trades, calculate_win_rate_from_trades, pnl_all_positions
from signal_generator import get_current_price, data_preparation
from risk_manager import get_current_price, get_current_balance, get_quantity,get_pnl_price,get_open_positions, check_instrument_positions,place_market_order, close_position, calculate_total_unrealised_pnl, close_all_trades
from datetime import datetime
import time
import oandapyV20
import oandapyV20.endpoints.pricing as pricing
import pandas as pd
import numpy as np
import joblib
from status import Status, Models

# ====== OANDA account details ======
access_token = "3f0f1b513d44797ff63c09d9da612561-6480f119d75e63cea1e420564d12b6f1"
account_id = "101-003-28603773-001"

accountID = account_id
access_token = access_token
client = oandapyV20.API(access_token=access_token, environment="practice")

# ====== Constants ======

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

# Library import:
models_15 = joblib.load("models_15mins.joblib")
model_15mins_features = ['DPO_20', 'THERMO_20_2_0.5', 'CFO_9', 'TRUERANGE_1', 'PDIST', 'BBB_5_2.0', 'RVI_14', 'SLOPE_1', 'BULLP_13', 'BOP']

# ===== Variables =====
# Variable to be changed 
# Risk reward (1:3) % based on prices
default_take_profit = 0.015
default_stop_loss = 0.005

target_pnl = 105000 
stoploss_pnl = 95000

# Setup
default_usd_pairs = ["EUR_USD","USD_JPY", "GBP_USD","AUD_USD"]

# trade_cycle
default_trade_cycle = 1
target_pnl = 10500
# order type
default_order_type = "MARKET"

# Lookback Count
# look back set as 20 to get the latest price action
default_lookback_count = 20

# ====== Trading Strategy ======

def trade_attempt(
        status: Status = Status.Inactive,
        model: Models = Models.FiveMin,
        usd_pairs: list = default_usd_pairs,
        take_profit: float = default_take_profit,
        stop_loss: float = default_stop_loss,
        trade_cycle: int = default_trade_cycle,
        order_type: str = default_order_type,
        lookback_count: int = default_lookback_count):
    print("--- Trading attempt: START ---")
    print("Configurable variables: ")
    print("Model=", model)
    print("Take Profit=", take_profit)
    print("Stop Loss=", stop_loss)

    if status == Status.Active:       
        try:
            print("Running strategy...")
            opening_balance = get_current_balance()
            start_time = datetime.now()
            open_datetime = datetime.now().date()

            positions_dict = get_open_positions()

            for instrument in usd_pairs:
                
                 # === Model Selection
                price = get_current_price(instrument)
                if model == Models.OneMin:
                    model_type = "models_1mins"
                    price_df = data_preparation(model_type, instrument,lookback_count)

                elif model == Models.FiveMin:
                    model_type = "models_5mins"
                    price_df = data_preparation(model_type, instrument,lookback_count)

                elif model == Models.FifteenMin:
                    model_type = "models_15mins"
                    price_df = data_preparation(model_type, instrument,lookback_count)

                elif model == Models.OneHour: 
                    model_type = "models_1hour"
                    price_df = data_preparation(model_type, instrument,lookback_count)

                else:   
                    model_type = "models_15mins"
                    price_df = data_preparation(model_type, instrument,lookback_count)

                # === end of model logic

                #find the last signal
                signal = price_df["prediction_on_next_close"].iloc[-1]
                positions_dict = get_open_positions()
                position_type = check_instrument_positions(positions_dict,instrument)

                #Determine position and create market order

                if position_type == "None": 
                    if signal == 1: 
                        quantity = get_quantity(instrument,signal)
                        pnl_price = get_pnl_price(instrument, signal,take_profit,stop_loss)
                        take_profit_price = pnl_price[0]
                        stop_loss_price = pnl_price[1]
                        place_market_order(instrument, order_type, quantity, take_profit_price, stop_loss_price)

                    elif signal == -1: 
                        quantity = get_quantity(instrument,signal)
                        pnl_price = get_pnl_price(instrument, signal,take_profit,stop_loss)
                        take_profit_price = pnl_price[0]
                        stop_loss_price = pnl_price[1]
                        place_market_order(instrument, order_type, quantity, take_profit_price, stop_loss_price)

                elif position_type == "Long":
                    if signal == 1: 
                        print ("Hold the trade")
                        
                    elif signal == -1: 
                        close_position = close_position(instrument, long_units='ALL', short_units='ALL')
                        quantity = get_quantity(instrument,signal)
                        pnl_price = get_pnl_price(instrument, signal,take_profit,stop_loss)
                        take_profit_price = pnl_price[0]
                        stop_loss_price = pnl_price[1]
                        place_market_order(instrument, order_type, quantity, take_profit_price, stop_loss_price)

                elif position_type == "Short":
                    if signal == 1: 
                        close_position = close_position(instrument, long_units='ALL', short_units='ALL')
                        quantity = get_quantity(instrument,signal)
                        pnl_price = get_pnl_price(instrument, signal,take_profit,stop_loss)
                        take_profit_price = pnl_price[0]
                        stop_loss_price = pnl_price[1]
                        place_market_order(instrument, order_type, quantity, take_profit_price, stop_loss_price)

                    elif signal == -1: 
                        print ("Hold the trade")
                else:
                    pass  
            
            #Calculate the pnl
            
            positions_dict = get_open_positions()
            long_pnl, short_pnl, total_pnl = calculate_total_unrealised_pnl(positions_dict)    

            print(f" Target:  {target_pnl:.2f} | StopLoss: {stoploss_pnl :.2f} | PNL:  {total_pnl:.2f} ") 
            #calculate returns 
            cycle_datetime = datetime.now().date()
            trade_days = (open_datetime - cycle_datetime).days

            annualised_returns = calculate_annualised_returns(opening_balance, trade_days)
            #print( "Annualised return is ", round(annualised_returns, 2) )

            #calculate draw_down
            transactions = fetch_transactions(start_time, datetime.now())
            df_equity = process_transactions(transactions, get_current_balance())
            df_drawdown = calculate_drawdowns(df_equity)
            max_drawdown = df_drawdown['drawdown_pct'].max()
            #print(f"Maximum Drawdown: {max_drawdown}%")

            #Calculate sharpe ratio
            #Fetch account changes
            df_returns = fetch_balance_changes(start_time, datetime.now())

            if not df_returns.empty:
                sharpe_ratio = calculate_sharpe_ratio(df_returns)
                print( "Sharpe Ratio is ", round(sharpe_ratio, 2) )
            else:
                print("No data available to calculate Sharpe Ratio.")

            #Calculate Win-rate
            closed_trades = fetch_closed_trades()
            win_rate = calculate_win_rate_from_trades(closed_trades)
            #print(f"Win Rate: {win_rate:.2f}%")

            #Update Time series PNL
            time_series = []
            pnl_series = []
            pnl = pnl_all_positions()
            time_series.append(datetime.now())
            pnl_series.append(pnl)

            time.sleep(trade_cycle)  # Wait for a minute before the next cycle

        except Exception as e:
            print(f"An error occurred: {e}")

    elif status == Status.Inactive:
        
        try: 
            print("Trade is still open")

            positions_dict = get_open_positions()
            long_pnl, short_pnl, total_pnl = calculate_total_unrealised_pnl(positions_dict)    

            print(f" Target:  {target_pnl:.2f} | StopLoss: {stoploss_pnl :.2f} | PNL:  {total_pnl:.2f} ")

        except Exception as e:
            print(f"An error occurred: {e}")

    else: 
        print("Closing all Trades")
        close_all_trades(client, accountID)
        print("Current balance: {:.2f}".format(get_current_balance()))
    
    print("--- Trading attempt: END ---")
