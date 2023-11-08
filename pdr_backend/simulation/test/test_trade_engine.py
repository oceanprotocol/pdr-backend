import os

from enforce_typing import enforce_types

from pdr_backend.simulation.data_ss import DataSS
from pdr_backend.simulation.model_ss import ModelSS
from pdr_backend.simulation.timeutil import timestr_to_ut
from pdr_backend.simulation.tradeutil import TradeParams, TradeSS
from pdr_backend.simulation.trade_engine import TradeEngine


@enforce_types
def test_TradeEngine(tmpdir):
    logpath = str(tmpdir)
    data_ss = DataSS(
        csv_dir=os.path.abspath("csvs"),  # use the usual data (worksforme)
        st_timestamp=timestr_to_ut("2023-06-22"),
        fin_timestamp=timestr_to_ut("2023-06-24"),
        max_N_train=500,
        N_test=100,
        Nt=2,
        usdcoin="USDT",
        timeframe="5m",
        signals=["open", "close"],
        coins=["ETH", "BTC"],
        exchange_ids=["binanceus"],
        yval_exchange_id="binanceus",
        yval_coin="BTC",
        yval_signal="close",
    )

    model_ss = ModelSS("LIN")

    trade_pp = TradeParams(
        fee_percent=0.0,  # Eg 0.001 is 0.1%. Trading fee (simulated)
        init_holdings={"USDT": 100000.0, "BTC": 0.0},
    )

    trade_ss = TradeSS(
        do_plot=False,  # plot at end?
        logpath=logpath,
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
