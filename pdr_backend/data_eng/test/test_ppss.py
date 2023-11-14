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
    - binance oh BTC/USDT
    - kraken c ETH/USDT,TRX/DAI
#    - binance c DOT/USDT
  st_timestr: 2019-09-13_04:00
  fin_timestr: now
  max_n_train: 5000
  autoregressive_n : 10
  csv_dir: csvs

model_ss:
  approach: LIN

trade_pp: # sim only, not bots
  fee_percent: 0.01
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
    assert ppss.data_pp.test_n == 200

    assert ppss.data_ss.input_feeds_strs == ["binance oh BTC/USDT",
                                             "kraken c ETH/USDT,TRX/DAI"]
    assert ppss.data_ss.st_timestr == "2019-09-13_04:00"
    assert ppss.data_ss.fin_timestr == "now"
    assert ppss.data_ss.max_n_train == 5000
    assert ppss.data_ss.autoregressive_n == 10
    assert ppss.data_ss.csv_dir_in == "csvs"

    assert ppss.model_ss.model_approach == "LIN"

    assert ppss.trade_pp.fee_percent == 0.01
    assert ppss.trade_pp.init_holdings_strs == ["100000 USDT", "0 BTC"]

    assert ppss.trade_ss.buy_amt_str == "10 USDT"
    
    assert ppss.sim_ss.do_plot
    assert ppss.sim_ss.logpath_in == "./"

    
