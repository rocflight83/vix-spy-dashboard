import vectorbtpro as vbt
from datetime import date, datetime, timedelta
import pytz
import pandas as pd
import numpy as np
import scipy.stats as st
import requests
import io
import calendar
import pandas_ta as ta
import talib
import plotly.graph_objects as go
# from sklearn import datasets, linear_model
# from sklearn.metrics import mean_squared_error, r2_score
from dateutil.relativedelta import relativedelta
from itertools import product
from dateutil import tz, parser
from numba import njit
from collections import deque
from scipy.signal import argrelextrema
from pandas.tseries.offsets import CustomBusinessDay
import scipy.optimize as opt
import json
import requests
import math
from yahooquery import Ticker

# TradeStation credentials now loaded from environment variables
# Use the new backend API for secure credential management

def get_access_token():
    url = "https://signin.tradestation.com/oauth/token"

    payload=f'grant_type=refresh_token&client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}&refresh_token={REFRESH_TOKEN}'
    headers = {
      'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    # print(response.text)
    response_data = response.json()
    return response_data['access_token']

vix = Ticker('^VIX')
end_date_str = datetime.now().strftime('%Y-%m-%d')
vix_hist = vix.history(period='5d', interval='1d', end=end_date_str)
vixlen = len(vix_hist)

if vix_hist.iloc[vixlen-1].open > vix_hist.iloc[vixlen-2].close:
    today = date.today()
    currtime = datetime.now(pytz.timezone('US/Eastern'))

    sym = 'SPY'
    proximity = 20
    optpref = str(today.year)[2:]+str(today.month).zfill(2)+str(today.day).zfill(2)

    access_token = get_access_token()

    url = f"https://api.tradestation.com/v3/marketdata/stream/options/chains/{sym}"

    headers = {"Authorization": f'Bearer {access_token}' }

    params = {
        "expiration": str(today.month).zfill(2)+'-'+str(today.day).zfill(2)+'-'+str(today.year),
        "strikeProximity": f'{proximity}',
    }

    response = requests.request("GET", url, headers=headers, params=params, stream=True)

    chain = pd.DataFrame(columns=['Strike', 'Side', 'Delta', 'Bid', 'Ask', 'Mid'])
    i = 1

    # print(response.text)

    for line in response.iter_lines():
        if line:
            data = json.loads(line)
            # if 'Delta' in data:
            chain.loc[len(chain)] = [data['Strikes'][0], data['Side'], data['Delta'], data['Bid'], data['Ask'], 
                                    str((float(data['Ask']) + float(data['Bid']))/2)]
            i+=1
        if i > proximity * 4:
            break

    chain = chain.set_index(['Strike', 'Side'])

    chain['DDiff'] = [abs(float(s) - .3) if float(s) > 0 else abs(float(s) + .3) for s in chain.Delta]

    putindex = chain[chain.index.get_level_values(1) == 'Put']['DDiff'].idxmin()
    callindex = chain[chain.index.get_level_values(1) == 'Call']['DDiff'].idxmin()
    putstrike = putindex[0]
    putwingstrike = str(int(putstrike) - 10)
    callstrike = callindex[0]
    callwingstrike = str(int(callstrike) + 10)
    mputprice = chain.loc[putindex].Bid
    mcallprice = chain.loc[callindex].Bid
    mputwingprice = chain.loc[(putwingstrike, 'Put')].Ask
    mcallwingprice = chain.loc[(callwingstrike, 'Call')].Ask
    mmaxprofit = float(mputprice) + float(mcallprice) - float(mputwingprice) - float(mcallwingprice)
    mmaxprofit = str(math.floor(mmaxprofit * 100)/100)
    mmaxloss = str(10.0 - float(mmaxprofit))
    lputprice = chain.loc[putindex].Mid
    lcallprice = chain.loc[callindex].Mid
    lputwingprice = chain.loc[(putwingstrike, 'Put')].Mid
    lcallwingprice = chain.loc[(callwingstrike, 'Call')].Mid
    lmaxprofit = float(lputprice) + float(lcallprice) - float(lputwingprice) - float(lcallwingprice)
    lmaxprofit = str(math.floor(lmaxprofit * 100)/100)
    lmaxloss = str(10.0 - float(lmaxprofit))

    rt = 'sim-'
    account = 'SIM2818191M'

    access_token = get_access_token()

    url = f"https://{rt}api.tradestation.com/v3/orderexecution/orders"

    payload = { 
            "AccountID": f'{account}', 
            "OrderType": "Market", 
            # "OrderType": "Limit",
            # "LimitPrice": lmaxprofit,
            "TimeInForce": { 
                "Duration": "DAY" 
            }, 
            "Legs": [
                {"Symbol": f'{sym}' + ' ' + f'{optpref}' + 'P' + f'{putwingstrike}',
                "Quantity": 1,
                "TradeAction": "BUYTOOPEN"
                }, 
                {"Symbol": f'{sym}' + ' ' + f'{optpref}' + 'P' + f'{putstrike}',
                "Quantity": 1,
                "TradeAction": "SELLTOOPEN"
                }, 
                {"Symbol": f'{sym}' + ' ' + f'{optpref}' + 'C' + f'{callstrike}',
                "Quantity": 1,
                "TradeAction": "SELLTOOPEN"
                }, 
                {"Symbol": f'{sym}' + ' ' + f'{optpref}' + 'C' + f'{callwingstrike}',
                "Quantity": 1,
                "TradeAction": "BUYTOOPEN"
                }
            ],
            "OSOs": [
                {"Type": "Normal",
                "Orders": [
                    {
                        "AccountID": f'{account}', 
                        "OrderType": "Limit", 
                        "LimitPrice": str(math.floor(float(mmaxprofit)*.25*100)/100),
                        "TimeInForce": { 
                            "Duration": "DAY" 
                        }, 
                        "Legs": [
                            {"Symbol": f'{sym}' + ' ' + f'{optpref}' + 'P' + f'{putwingstrike}',
                            "Quantity": 1,
                            "TradeAction": "SELLTOCLOSE"
                            }, 
                            {"Symbol": f'{sym}' + ' ' + f'{optpref}' + 'P' + f'{putstrike}',
                            "Quantity": 1,
                            "TradeAction": "BUYTOCLOSE"
                            }, 
                            {"Symbol": f'{sym}' + ' ' + f'{optpref}' + 'C' + f'{callstrike}',
                            "Quantity": 1,
                            "TradeAction": "BUYTOCLOSE"
                            }, 
                            {"Symbol": f'{sym}' + ' ' + f'{optpref}' + 'C' + f'{callwingstrike}',
                            "Quantity": 1,
                            "TradeAction": "SELLTOCLOSE"
                            }
                        ]
                    }
                ]}
            ]
        }


    headers = {
        "content-type": "application/json",
        "Authorization": f'Bearer {access_token}'
    }

    response = requests.request("POST", url, json=payload, headers=headers)