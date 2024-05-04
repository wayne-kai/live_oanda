import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from Relative_Functions import OandaAPI, Delta_Data

from live_trading.status import Status, Models
import requests

access_token = "3f0f1b513d44797ff63c09d9da612561-6480f119d75e63cea1e420564d12b6f1"
account_id = "101-003-28603773-001"

api_client = OandaAPI(access_token=access_token)
api_delta = Delta_Data()

st.set_page_config(layout="wide")

# initialize state variables
if 'current_pair' not in st.session_state:
    st.session_state['current_pair'] = "EUR_USD"

if 'trading_status' not in st.session_state:
    st.session_state['trading_status'] = Status.Unknown

def disable_button(button: str):
    # print("button: ", button)
    if button == "start_button":
        return st.session_state['trading_status'] == Status.Active
    elif button == "pause_button":
        return st.session_state['trading_status'] != Status.Active or st.session_state['trading_status'] == Status.Unknown
    elif button == "stop_button":
        return st.session_state['trading_status'] == Status.Stop or st.session_state['trading_status'] == Status.Unknown

# ********************************************* sidebar begin *********************************************
st.sidebar.title("Operation Panel")

if st.sidebar.button("EUR-USD 🇪🇺🇺🇸", on_click=None, type="secondary", use_container_width=True):
    # st.sidebar.write("You have selected EUR-USD 🇪🇺🇺🇸")
    st.session_state['current_pair'] = "EUR_USD"
if st.sidebar.button("USD/JPY 🇺🇸🇯🇵", on_click=None, type="secondary", use_container_width=True):
    # st.sidebar.write("You have selected USD/JPY 🇺🇸🇯🇵")
    st.session_state['current_pair'] = "USD_JPY"
if st.sidebar.button("GBP/USD 🇬🇧🇺🇸", on_click=None, type="secondary", use_container_width=True):
    # st.sidebar.write("You have selected GBP/USD 🇬🇧🇺🇸")
    st.session_state['current_pair'] = "GBP_USD"
if st.sidebar.button("AUD/USD 🇦🇺🇺🇸", on_click=None, type="secondary", use_container_width=True):
    # st.sidebar.write("You have selected AUD/USD 🇦🇺🇺🇸")
    st.session_state['current_pair'] = "AUD_USD"

st.sidebar.markdown("---")

# TODO: move where?
# summary_info_sidebar = api_client.get_account_summary()
# st.sidebar.dataframe(data=summary_info_sidebar,use_container_width=True)


# ************************************** Trading Strategy Buttons ****************************************


# http request to activate the trading strategy
def send_request(
        status: Status,
        model: Models = Models.Unknown,
        take_profit: float = 0.003,
        stop_loss: float = 0.001,):
    path = "deactivate"
    if status == Status.Active:
        path = "activate"
    elif status == Status.Stop:
        path = "stop"

    url = "http://127.0.0.1:5003/" + path
    
    try:
        # Send the POST request with error handling
        response = requests.post(url, json={
            "model": model.value, 
            "take_profit": take_profit, 
            "stop_loss": stop_loss})
        response.raise_for_status()  # Raise an exception for non-200 status codes

        print("success")
        st.session_state['trading_status'] = status

    except requests.exceptions.RequestException as e:
        # Handle errors during request execution (e.g., connection issues)
        print(f"Error: An error occurred during the request - {e}")


# input
# - model:
#    - 1 min
#    - 15 min
#    - 5 min
# - risk & reward ra. (take profit/stop loss)
model_options = {
    Models.OneMin: "1 min",
    Models.FiveMin: "5 min",
    Models.FifteenMin: "15 min",
    Models.OneHour: "1 hour",
}

selected_model = st.sidebar.selectbox(
    label="Select model",
    options=model_options.keys(), # values
    format_func=lambda x: model_options[x], # display
    index=2,
    disabled=disable_button("start_button"),
)

# rr_ratio = st.sidebar.number_input("Risk/Reward ratio", value=2, placeholder="Insert a number", disabled=disable_button("start_button"))
take_profit = st.sidebar.number_input("Take Profit", value=0.002, step=1e-3, format="%.3f", placeholder="Insert a number", disabled=disable_button("start_button"))
stop_loss = st.sidebar.number_input("Stop Loss", value=0.001, step=1e-3, format="%.3f", placeholder="Insert a number", disabled=disable_button("start_button"))

def trading_buttons_callback(status: Status):
    global selected_model, take_profit, stop_loss
    send_request(status, selected_model, take_profit, stop_loss)

st.sidebar.button("Start", key="start_button", help="Click to start", use_container_width=True, disabled=disable_button("start_button"),
                  on_click=trading_buttons_callback, args=(Status.Active,))

st.sidebar.button("Pause", key="pause_button", help="Click to pause", use_container_width=True, disabled=disable_button("pause_button"),
                     on_click=trading_buttons_callback, args=(Status.Inactive,))

st.sidebar.button("Stop", key="stop_button", help="Click to stop", use_container_width=True, disabled=disable_button("stop_button"),
                     on_click=trading_buttons_callback, args=(Status.Stop,)) 

def display_trading_status():
    if st.session_state['trading_status'] == Status.Active:
        st.sidebar.success("Trading Strategy is Running")
    elif st.session_state['trading_status'] == Status.Inactive:
        st.sidebar.success("Trading Strategy is Paused")
    elif st.session_state['trading_status'] == Status.Stop:
        st.sidebar.error("Trading Strategy has been Stopped")
display_trading_status()

# ********************************************* sidebar end *********************************************




# ********************************************* main page begin *****************************************

# 1. Real Time Prices

@st.experimental_fragment(run_every=5)
def show_price():
    prices = api_client.get_prices()
    price_delta = api_delta.get_price_delta(prices)
    tp1, tp2, tp3, tp4 = st.columns(4)
    with tp1:
        st.metric(label="EUR/USD", value=round(float(prices['EUR_USD']),4), delta=price_delta['EUR_USD'])
    with tp2:
        st.metric(label="USD/JPY", value=round(float(prices['USD_JPY']),4), delta=price_delta['USD_JPY'])
    with tp3:
        st.metric(label="GBP/USD", value=round(float(prices['GBP_USD']),4), delta=price_delta['GBP_USD'])
    with tp4:
        st.metric(label="AUD/USD", value=round(float(prices['AUD_USD']),4), delta=price_delta['AUD_USD'])

show_price()


# ================================== CandlePlot ==================================
st.header("CandlePlot")
import plotly.graph_objects as go

from app import update_figure

@st.experimental_fragment(run_every=10)
def update_candle_plot():
    granularity = 'S5'
    if selected_model == Models.OneMin:
        granularity = "M1"
    elif selected_model == Models.FiveMin:
        granularity = "M5"
    elif selected_model == Models.FifteenMin:
        granularity = "M15"
    elif selected_model == Models.OneHour:
        granularity = "H1"
    st.plotly_chart(update_figure(tickerChoice=st.session_state['current_pair'], granularity=granularity), use_container_width=True)
update_candle_plot()


# 2. Strategy Explanation
@st.cache_data
def read_strategy_explaination():
    with open('./materials/Strategy_Explaination.txt', 'r') as f:
        return f.read()
    
with st.expander("Strategy Description"):
    strategy_explaination = read_strategy_explaination()
    st.write(strategy_explaination)
    # st.image("https://static.streamlit.io/examples/dice.jpg")


# 3. Performance Metrics
st.header("Performance Metrics")

@st.experimental_fragment(run_every=30)
def account_summary():

    summary_info_api = api_client.get_account_summary()

    #TODO update the hard-coded data source
    metrics_data = {"balance": round(float(summary_info_api['balance']),2),
                    "positionValue": round(float(summary_info_api['positionValue']),2),
                    "pl":   round(float(summary_info_api['pl']),2),
                    "unrealizedPL": round(float(summary_info_api['unrealizedPL']),2),
                    "annualized_return": float(summary_info_api['annualized_return']),
                    "max_drawdown": float(summary_info_api['max_drawdown']),
                    "sharpe_ratio": float(summary_info_api['sharpe_ratio']),
                    "win_rate": float(summary_info_api['win_rate']) 
                }
    
    metrics_data_delta = api_delta.get_summary_info_delta(metrics_data)
    

    # data get from API
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Total Capital", value=metrics_data["balance"], delta=metrics_data_delta["balance"])
    with col2:
        st.metric(label="Position Value", value=metrics_data["positionValue"], delta=metrics_data_delta["positionValue"])
    with col3:
        st.metric(label="Realized P&L", value=metrics_data["pl"], delta=metrics_data_delta["pl"])
    with col4:
        st.metric(label="Unrealized P&L", value=metrics_data["unrealizedPL"], delta=metrics_data_delta["unrealizedPL"])

    # data get from calculation
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.metric(label="Annualized Return", value=metrics_data["annualized_return"], delta=metrics_data_delta["annualized_return"], delta_color="inverse")
    with col6:
        st.metric(label="Maximum Drawdown", value=metrics_data["max_drawdown"], delta=metrics_data_delta["max_drawdown"], delta_color="inverse")
    with col7:
        st.metric(label="Sharpe Ratio", value=metrics_data["sharpe_ratio"], delta=metrics_data_delta["sharpe_ratio"], delta_color="inverse")
    with col8:
        st.metric(label="Win Rate(%)", value=metrics_data["win_rate"], delta=metrics_data_delta["win_rate"], delta_color="inverse")

account_summary()



# 5. Order History
st.header("Historical Orders")
# re-check the order history every 15 seconds
@st.experimental_fragment(run_every=30)
def get_order_history_():
    order_history = api_client.get_order_history()
    # return order_history
    # order_history = get_order_history_() # details in Relative_Functions.py

    st.dataframe(data=order_history,
                use_container_width=True,
                hide_index=None,
                column_order=None,
                column_config=None
                )
get_order_history_()


# # 6. Other Visualizations
# st.header("Performance Metrics")


# ********************************************* main page end *******************************************