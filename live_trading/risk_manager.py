import oandapyV20
import oandapyV20.endpoints.positions as positions
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.trades as trades
import oandapyV20.endpoints.pricing as pricing
from oandapyV20.endpoints.accounts import AccountDetails
from oandapyV20.exceptions import V20Error

access_token = "3f0f1b513d44797ff63c09d9da612561-6480f119d75e63cea1e420564d12b6f1"
account_id = "101-003-28603773-001"


accountID = account_id
access_token = access_token
client = oandapyV20.API(access_token=access_token, environment="practice")

def get_current_price(instrument):
    params = {
        "instruments": instrument
    }
    request = pricing.PricingInfo(accountID=account_id, params=params)
    response = client.request(request)

    if 'prices' in response and response['prices']:
        return float(response['prices'][0]['bids'][0]['price'])

    return None

def get_instrument_precision(instrument):
    instrument_precision = {
        'EUR_USD': 4,
        'USD_JPY': 3,   
        'GBP_USD': 4,
        'AUD_USD': 4,
        'NZD_USD': 4,
        'USD_HKD': 4,
        'USD_SGD': 4,
        'USD_MXN': 4,
        'USD_THB': 3,
        'USD_ZAR': 4,
        #'USD_RUB': 4,
        #'BTC_USD': 1
        }
    return instrument_precision.get(instrument)  # Set a default precision value if instrument not found


def get_current_balance():
    request = AccountDetails(accountID=accountID)
    response = client.request(request)

    if response and 'account' in response:
        account_info = response['account']
        balance = float(account_info['balance'])
        return balance
        
    return None


def get_quantity(instrument, trade_direction):

    trade_currency_2 = instrument[4:]
    position_size=None
    # A more complex calculation can be done 

    if "USD" in trade_currency_2:
        position_size = 100000
    elif "JPY" in trade_currency_2:
        position_size = 50000
    else:
        print("Unsupported currency in the denominator")
        position_size = None
    
    if trade_direction == "BUY":
        position_size = position_size 
    else:
        position_size = -position_size

    return position_size

def get_pnl_price(instrument, trade_direction,take_profit,stop_loss):
    current_price = get_current_price(instrument)
    take_profit_percentage = take_profit
    stop_loss_percentage = stop_loss
    
    # if trade_direction == "BUY":
    if trade_direction == 1:
        take_profit_price = round(current_price * (1 + take_profit_percentage), get_instrument_precision(instrument))
        stop_loss_price = round(current_price * (1 - stop_loss_percentage), get_instrument_precision(instrument))
    # trade_direction == "SELL"
    elif trade_direction == "-1":
        take_profit_price = round(current_price * (1 - take_profit_percentage), get_instrument_precision(instrument))
        stop_loss_price = round(current_price * (1 + stop_loss_percentage), get_instrument_precision(instrument))
    else:
        print("Hold")
        return
    #print(stop_loss_price, take_profit_price)

    return take_profit_price, stop_loss_price

def get_open_positions():
    request = positions.OpenPositions(accountID=account_id)
    response = client.request(request)
    open_positions = response.get("positions", [])
    return open_positions
#Check for any open position for individual instrument 

def check_instrument_positions(open_positions,instrument):
    if open_positions:  
        positions_summary = open_positions['positions']
        for pos in positions_summary:
            if pos['instrument'] == instrument:
                print(pos['long']['units'])
                if float(pos['long']['units']) == 0 : 
                    position_type = "Short"
                elif float(pos['short']['units']) == 0 :
                    position_type = "Long"
                else:
                    position_type = "None"
            else:
                position_type = "None"
    else:
        position_type = "None"
    return position_type

def close_position(instrument, long_units=None, short_units=None):
    """
    Close positions for a specific instrument with flexible unit specifications.

    """
    data = {
        "longUnits": str(long_units) if long_units else "0",  # Converts None or unspecified to '0'
        "shortUnits": str(short_units) if short_units else "0"  # Converts None or unspecified to '0'
    }
    
    # Handle the 'ALL' case separately
    if long_units == 'ALL':
        data["longUnits"] = 'ALL'
    if short_units == 'ALL':
        data["shortUnits"] = 'ALL'

    request = positions.PositionClose(accountID=account_id, instrument=instrument, data=data)
    close_response = client.request(request)
    if "errorMessage" in close_response:
        print("Error occurred closing order:", close_response["errorMessage"])
    else:
        print("Close position transaction completed:", close_response)

    return close_response


def calculate_total_unrealised_pnl(positions_dict):
    long_pnl = 0
    short_pnl = 0
    total_pnl = 0

    for position in positions_dict:
        long_unrealized_pnl = float(position['long']['unrealizedPL'])
        short_unrealized_pnl = float(position['short']['unrealizedPL'])

        long_pnl += long_unrealized_pnl
        short_pnl += short_unrealized_pnl
        total_pnl = long_pnl + short_pnl

    return long_pnl, short_pnl, total_pnl

def place_market_order(instrument,order_type, units, take_profit_price, stop_loss_price):
    data = {
        "order": {
            "units": str(units),
            "instrument": instrument,
            "timeInForce": "FOK",
            "type": order_type, #can change to order if required
            "positionFill": "DEFAULT",
            "takeProfitOnFill": {
                "price": str(float(take_profit_price)),
            },
            "stopLossOnFill": {
                "price": str(float(stop_loss_price)),
            }
        }
    }
    
    try:
        request = orders.OrderCreate(accountID, data=data)
        response = client.request(request)
        # print(response)
        print("Oanda Orders placed successfully!")
        subject = "Oanda Trades Initiated"
        body = "Oanda Trades Initiated"
        return response
        #send_email_notification(subject, body)
    except V20Error as e:
        print("Error placing Oanda orders:")
        print(e)
        subject = "Failed to Take Oanda Trades"
        body = "Failed to Take Oanda Trades"
        #send_email_notification(subject, body)


def close_all_trades(client, account_id):
    # Get a list of all open trades for the account
    trades_request = trades.OpenTrades(accountID=account_id)
    response = client.request(trades_request)

    if len(response['trades']) > 0:
        for trade in response['trades']:
            trade_id = trade['id']
            try:
                # Create a market order to close the trade
                data = {
                    "units": "ALL",
                }
                order_request = trades.TradeClose(accountID=account_id, tradeID=trade_id, data=data)
                response = client.request(order_request)
                print(f"Trade {trade_id} closed successfully.")
            except oandapyV20.exceptions.V20Error as e:
                print(f"Failed to close trade {trade_id}. Error: {e}")
    else:
        print("No open trades to close.")

