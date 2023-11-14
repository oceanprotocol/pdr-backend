import os
from enforce_typing import enforce_types

from pdr_backend.data_eng.ppss import PPSS

@enforce_types
def test1(tmpdir):
    # set string
    ppss_str = """
data_pp:
  timeframe: 1h
  predict_feed: binance c BTC/USDT
  test_n : 200 # sim only, not bots

data_ss:
  input_feeds :
    - binance ohlcv BTC/USDT
    - binance c ETH/USDT,TRX/USDT,ADA/USDT
#    - binance c DOT/USDT
    - kraken ohlcv BTC/USDT
  st_timestr: 2019-09-13_04:00
  fin_timestr: now
  max_n_train: 5000
  autoregressive_n : 10
  csv_dir: csvs

model_ss:
  approach: LIN

trade_pp: # sim only, not bots
  fee_percent: 0.0
  init_holdings:
    - 100000 USDT
    - 0 BTC

trade_ss:
  buy_amt: 10 USDT

sim_ss:
  do_plot: True
"""
    # put string to file
    fname = os.path.join(tmpdir, "ppss.yaml")
    f = open(fname, "a")
    f.write(ppss_str)
    f.close()

    # create PPSS object from file
    ppss = PPSS(fname)

    assert ppss.data_pp.timeframe == "1h"
    assert ppss.data_pp.predict_feed_str == "binance c BTC/USDT"

    # FIXME: add the rest

    
