import os

import kaiko

KAIKO_KEY = os.getenv("KAIKO_KEY")
assert KAIKO_KEY is not None

# Setting a client with your API key
kc = kaiko.KaikoClient(api_key=KAIKO_KEY)

# Getting some simple daily candles
ds = kaiko.Aggregates(type_of_aggregate = 'COHLCV_VWAP', exchange = 'cbse', instrument = 'btc-usdt', start_time='2020-08', interval='1d', client=kc)

# Retrieve the dataframe containing the data
ds.df
