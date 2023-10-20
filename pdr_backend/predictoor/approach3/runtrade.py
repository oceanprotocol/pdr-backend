#!/usr/bin/env python
import os

from pdr_backend.predictoor.approach3.data_ss import DataSS
from pdr_backend.predictoor.approach3.model_ss import ModelSS
from pdr_backend.predictoor.approach3.timeutil import timestr_to_ut
from pdr_backend.predictoor.approach3.tradeutil import TradeParams, TradeSS
from pdr_backend.predictoor.approach3.trade_engine import TradeEngine

# Backlog is in backlog.py

# ==================================================================
# params that I change

data_ss = DataSS(
    csv_dir=os.path.abspath("csvs"),
    st_timestamp=timestr_to_ut("2022-06-30"),  # 2019-09-13_04:00 earliest
    fin_timestamp=timestr_to_ut("now"),  # 'now','2023-06-21_17:55'
    max_N_train=5000,  # 50000 # if inf, only limited by data available
    N_test=200,  # 50000 . num points to test on, 1 at a time (online)
    Nt=10,  # eg 10. model inputs Nt past pts z[t-1], .., z[t-Nt]
    usdcoin="USDT",
    timeframe="1h",
    signals=["close"],  # ["open", "high","low", "close", "volume"],
    coins=["ETH", "BTC"],
    exchange_ids=["binanceus"],
    yval_exchange_id="binanceus",
    yval_coin="BTC",
    yval_signal="close",
)

model_ss = ModelSS("LIN")  # PREV, LIN, GPR, SVR, NuSVR, LinearSVR

trade_pp = TradeParams(
    fee_percent=0.00,  # Eg 0.001 is 0.1%. Trading fee (simulated)
    init_holdings={"USDT": 100000.0, "BTC": 0.0},
)

trade_ss = TradeSS(
    do_plot=True,  # plot at end?
    logpath=os.path.abspath("./"),
    buy_amt_usd=100000.00,  # How much to buy at a time. In USD
)

# ==================================================================
# print setup
print(f"data_ss={data_ss}")
print(f"model_ss={model_ss}")
print(f"trade_pp={trade_pp}")
print(f"trade_ss={trade_ss}")

# ==================================================================
# do work
trade_engine = TradeEngine(data_ss, model_ss, trade_pp, trade_ss)

trade_engine.run()
