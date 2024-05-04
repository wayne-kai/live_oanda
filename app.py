# Raw Package
import numpy as np
import pandas as pd
from pandas_datareader import data as pdr
 
# Market Data 
import yfinance as yf
 
#Graphing/Visualization
import datetime as dt 
import plotly.graph_objs as go 
 
# Override Yahoo Finance 
yf.pdr_override()
 
from datetime import date
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Internal Package
from data_fetcher import fetch_data

def makeCandlestick(fig, stockDF):
    #sets parameters for subplots
    fig = make_subplots(rows = 2, cols = 1, shared_xaxes = True,
                    vertical_spacing = 0.01,
                    row_heights = [0.8,0.2])#, 0.1, 0.15, 0.15
 
 
    #plots candlestick values using stockDF
    fig.add_trace(go.Candlestick(x = stockDF.index,
                                 open = stockDF['Open'],
                                 high = stockDF['High'],
                                 low = stockDF['Low'],
                                 close = stockDF['Close'],
                                 name = 'Open/Close'))
    
    return fig

def makeMA(fig, stockDF):
    #create moving average values
    stockDF["MA5"] = stockDF["Close"].rolling(window = 5).mean()
    stockDF["MA20"] = stockDF["Close"].rolling(window = 20).mean()
 
    #plots moving average values; the 50-day and 200-day averages
    #are visible by default, and the 5-day and 15-day are accessed via legend
    fig.add_trace(go.Scatter(x = stockDF.index, y = stockDF['MA5'], opacity = 0.4, 
                        line = dict(color = 'blue', width = 2), name = 'MA 5'))
             
    fig.add_trace(go.Scatter(x = stockDF.index, y = stockDF['MA20'], opacity = 0.7, 
                        line = dict(color = 'orangered', width = 2), name = 'MA 15'))

    return fig
 
def makeVolume(fig, stockDF):
    #sets colors of volume bars
    colors = ['green' if row['Open'] - row['Close'] >= 0
          else 'red' for index, row in stockDF.iterrows()]
 
 
    #Plot volume trace
    fig.add_trace(go.Bar(x = stockDF.index,
                         y = stockDF['Volume'],
                         marker_color = colors,
                         showlegend = False,
                         name = "Volume"
                         ), row = 2, col = 1) # row & col to indicate which figure to put in, default: row = 1, col = 1
 
    return fig

def makeCurrentPrice(fig, stockDF):
    #Plots the last closing price of stock 
    fig.add_trace(go.Scatter(x = stockDF.index,
              y = [stockDF['Close'].iat[-1] for price in range(len(stockDF))],
              opacity = 0.7, line = dict(color = 'red', width = 2, dash = 'dot'),
              name = "Current Price: " + str(round(stockDF['Close'].iat[-1], 2))))
     
 
    return fig
 
def graphLayout(fig, choice):
    #Sets the layout of the graph and legend
    fig.update_layout(title_text = choice + ' Price Action', 
                  title_x = 0.5, 
                #   legend_title_text = "Legend Items",
                  dragmode = "pan", 
                  xaxis_rangeslider_visible = False, 
                  hovermode = "x", 
                  legend = dict(bgcolor="#E2E2E2",
                           bordercolor="Black",
                           borderwidth=2,
                           font=dict(size=7))
                                
                 )
 
    subplotLabels(fig)
 
    return fig
def subplotLabels(fig):
    #Sets subplot labels
    fig.update_yaxes(title_text = "Price", row = 1, col = 1)
    fig.update_yaxes(title_text = "Volume", row = 2, col = 1)
    fig.update_yaxes(title_text = "RSI", row = 3, col = 1)
    fig.update_yaxes(title_text = "MACD", showgrid = False, row = 4, col = 1)
 
    return fig
 
 
def xAxes(fig):
    #Remove none trading days from dataset and sets behavior for x-axis mouse-hovering
    fig.update_xaxes(rangebreaks = [dict(bounds = ["sat", "mon"])], 
                 autorange = True, 
                 showspikes = True, 
                 spikedash = "dot",
                 spikethickness = 1, 
                 spikemode = "across", 
                 spikecolor = "black")
     
    return fig
 
config = dict({'scrollZoom': True})

def update_figure(n=0, _n_intervals=0, tickerChoice='EUR_USD', granularity='S5'):
    #set choice to something if !isPostBack

    # CHANGE THIS TO INPUT
    lookback_count = 120
 
    #make stockDF    
    stockDF = fetch_data(tickerChoice, granularity=granularity, lookback_count=lookback_count)

    #make go Figure object as fig
    fig = go.Figure()
 
    #make and plot candlestick chart
    fig = makeCandlestick(fig, stockDF)
 
    #update layout properties
    fig = graphLayout(fig, tickerChoice.upper())
 
    #updates x-axis parameters
    fig = xAxes(fig)
 
    #make and plot subplots charts and moving averages
    fig = makeMA(fig, stockDF)
    fig = makeVolume(fig, stockDF)
 
    #make and plot stock's last closing price
    fig = makeCurrentPrice(fig, stockDF)
     
    return fig