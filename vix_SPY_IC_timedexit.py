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
import re

CLIENT_ID = 'o4haO6Ax6ZkXwwVJC62bI4rBxfzzgaOM'
CLIENT_SECRET = 'it2Rp_nXMkM1bprXqwtbDYJ2awlbzPaX5SsKpq2hrV23agKWdVOSw19kYuJa56ab'
REFRESH_TOKEN = 'jKfddrd5FnWPG8tMURJ1Xgmo4DmP7zZLvR8TaEl0HrsBy'

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

sym = 'SPY'
rt = 'sim-'
account = 'SIM2818191M'

access_token = get_access_token()
url = f"https://{rt}api.tradestation.com/v3/brokerage/accounts/{account}/orders"
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.request("GET", url, headers=headers)
orders = response.json()['Orders']

for i in range(len(orders)):
        if (orders[i]['StatusDescription'] == 'Received') and (orders[i]['Legs'][0]['Underlying'] == sym):
            orderID = orders[i]['OrderID']
            url = f"https://{rt}api.tradestation.com/v3/orderexecution/orders/{orderID}"
            response = requests.request("DELETE", url, headers=headers)

url = f"https://{rt}api.tradestation.com/v3/brokerage/accounts/{account}/positions" 
response = requests.request("GET", url, headers=headers)
positions = response.json()['Positions']

exitlegs = 0

for i in range(len(positions)):
    if exitlegs < 4:
        symbol = positions[i]['Symbol']
        if symbol[:3] == sym:
            qty = positions[i]['Quantity'] # find qty remaining in position
            qty = re.sub(r'\D', '', qty) # quanty returned a negative number when position is short, need to convert to positive number
            ls = positions[i]['LongShort']
            ta = 'SELLTOCLOSE' if ls == 'Long' else 'BUYTOCLOSE'
            url = f"https://{rt}api.tradestation.com/v3/orderexecution/orders"
            if ((ls == 'Long') and (positions[i]['Bid'] == '0')) or ((ls == 'Short') and (positions[i]['Ask'] == '0')): 
                payload = { 
                    "AccountID": f'{account}', 
                    "OrderType": "Limit", 
                    "LimitPrice": positions[i]['Last'],
                    "TimeInForce": { 
                        "Duration": "GTC" 
                    }, 
                    "Route": "Intelligent",
                    "Legs": [{"Symbol": symbol,
                            "Quantity": qty,
                            "TradeAction": ta}]
                }
            else:
                payload = { 
                    "AccountID": f'{account}', 
                    "OrderType": "Market",
                    "TimeInForce": { 
                        "Duration": "GTC" 
                    }, 
                    "Route": "Intelligent",
                    "Legs": [{"Symbol": symbol,
                            "Quantity": qty,
                            "TradeAction": ta}]
                } 
            headers = {
                "content-type": "application/json",
                "Authorization": f'Bearer {access_token}'
                }
            response = requests.request("POST", url, json=payload, headers=headers)
            i += 1
    else:
        break