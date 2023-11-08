#!/usr/bin/env python
import os

from pdr_backend.util.env import parse_filters
from pdr_backend.simulation.data_ss import DataSS
from pdr_backend.simulation.model_ss import ModelSS
from pdr_backend.simulation.timeutil import timestr_to_ut
from pdr_backend.simulation.tradeutil import TradeParams, TradeSS
from pdr_backend.simulation.trade_engine import TradeEngine

# Backlog is in backlog.py

# ==================================================================
# params that I change

(pairs, timeframes, exchanges, _) = parse_filters()

if exchanges is None or len(exchanges) == 0:
    exchanges = ["binance"]

if pairs is None or len(pairs) == 0:
    pairs = ["BTC/USDT", "ETH/USDT"]

pairs = [i.split("/", maxsplit=1)[0] for i in pairs]

timeframe = "1h"

if timeframes is not None and len(timeframes) > 0:
    timeframe = timeframes[0]

print(f"Config: {pairs} {exchanges} {timeframe}")

data_ss = DataSS(
    csv_dir=os.path.abspath("csvs"),
    st_timestamp=timestr_to_ut("2022-06-30"),  # 2019-09-13_04:00 earliest
    fin_timestamp=timestr_to_ut("now"),  # 'now','2023-06-21_17:55'
    max_N_train=5000,  # 50000 # if inf, only limited by data available
    N_test=200,  # 50000 . num points to test on, 1 at a time (online)
    Nt=20,  # eg 10. model inputs Nt past pts z[t-1], .., z[t-Nt]
    usdcoin="USDT",
    timeframe=timeframe,
    signals=["close"],  # ["open", "high","low", "close", "volume"],
    coins=pairs,
    exchange_ids=exchanges,
    yval_exchange_id=exchanges[0],
    yval_coin=pairs[0],
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
