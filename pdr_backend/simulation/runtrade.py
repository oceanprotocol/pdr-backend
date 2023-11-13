#!/usr/bin/env python
import os

from pdr_backend.data_eng.data_pp import DataPP
from pdr_backend.data_eng.data_ss import DataSS
from pdr_backend.model_eng.model_ss import ModelSS
from pdr_backend.simulation.sim_ss import SimSS
from pdr_backend.simulation.trade_engine import TradeEngine
from pdr_backend.simulation.trade_pp import TradePP
from pdr_backend.simulation.trade_ss import TradeSS

# To play with simulation, simply change any of the arguments to any
# of the constructors below.
#
# - It does *not* use envvars PAIR_FILTER, TIMEFRAME_FILTER, or SOURCE_FILTER.
#   Why: to avoid ambiguity. Eg is PAIR_FILTER for yval_coin, or input data?

data_pp = DataPP(  # user-uncontrollable params, at data-eng level
    timeframe="1h",  # "5m" or "1h"
    yval_exchange_id="binance",  # "binance" or "kraken" or ...
    yval_coin="BTC",  # "BTC" or "ETH" or "TRX" or ...
    usdcoin="USDT",  # "USDT" or "USDC" or ..
    yval_signal="close",  # "close" or "open" or ...
    N_test=200,  # 50000 . num points to test on, 1 at a time (online)
)

data_ss = DataSS(  # user-controllable params, at data-eng level
    csv_dir=os.path.abspath("csvs"),  # eg "csvs". abs or rel loc'n of csvs dir
    st_timestr="2022-06-30",  # eg "2019-09-13_04:00" (earliest), "2019-09-13"
    fin_timestr="now",  # eg "now", "2023-09-23_17:55", "2023-09-23"
    max_n_train=5000,  # eg 50000. # if inf, only limited by data available
    autoregressive_n=20,  # eg 10. model inputs past pts z[t-1], .., z[t-ar_n]
    signals=["close"],  # for model input vars. eg ["open","high","volume"]
    coins=["BTC", "ETH"],  # for model input vars. eg ["ETH", "BTC"]
    exchange_ids=["binance"],  # for model input vars. eg ["binance", "mxc"]
)

model_ss = ModelSS(  # user-controllable params, at model-eng level
    "LIN"  # eg "LIN", "GPR", "SVR", "NuSVR", or "LinearSVR"
)

trade_pp = TradePP(  # user-uncontrollable params, at trading level
    fee_percent=0.00,  # Eg 0.001 is 0.1%. Trading fee (simulated)
    init_holdings={"USDT": 100000.0, data_pp.yval_coin: 0.0},
)

trade_ss = TradeSS(  # user-controllable params, at trading level
    buy_amt_usd=100000.00,  # How much to buy at a time. In USD
)

sim_ss = SimSS(  # user-controllable params, at sim level
    do_plot=True,  # plot at end?
    logpath=os.path.abspath("./"),  # where to save logs to
)

# ==================================================================
# print setup
print(f"data_pp={data_pp}")
print(f"data_ss={data_ss}")
print(f"model_ss={model_ss}")
print(f"trade_pp={trade_pp}")
print(f"trade_ss={trade_ss}")
print(f"sim_ss={sim_ss}")

# ==================================================================
# do work
trade_engine = TradeEngine(data_pp, data_ss, model_ss, trade_pp, trade_ss, sim_ss)

trade_engine.run()
