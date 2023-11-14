import os

from enforce_typing import enforce_types

from pdr_backend.data_eng.data_pp import DataPP
from pdr_backend.data_eng.data_ss import DataSS
from pdr_backend.data_eng.model_ss import ModelSS
from pdr_backend.simulation.trade_engine import TradeEngine
from pdr_backend.simulation.sim_ss import SimSS
from pdr_backend.simulation.trade_pp import TradePP
from pdr_backend.simulation.trade_ss import TradeSS


@enforce_types
def test_TradeEngine(tmpdir):
    logpath = str(tmpdir)

    data_pp = DataPP(  # user-uncontrollable params, at data level
        "5m",
        "binanceus c BTC/USDT",
        test_n=100,
    )

    data_ss = DataSS(  # user-controllable params, at data level
        ["binanceus oc ETH/USDT,BTC/USDT"],
        csv_dir=os.path.abspath("csvs"),  # use the usual data (worksforme)
        st_timestr="2023-06-22",
        fin_timestr="2023-06-24",
        max_n_train=500,
        autoregressive_n=2,
    )

    model_ss = ModelSS(  # user-controllable params, at model level
        "LIN",
    )

    trade_pp = TradePP(  # user-uncontrollable params, at trading level
        fee_percent=0.0,  # Eg 0.001 is 0.1%. Trading fee (simulated)
        init_holdings={"USDT": 100000.0, "BTC": 0.0},
    )

    trade_ss = TradeSS(  # user-controllable params, at trading level
        buy_amt_usd=100000.00,  # How much to buy at a time. In USD
    )

    sim_ss = SimSS(  # user-controllable params, at sim level
        do_plot=False,  # plot at end?
        logpath=logpath,  # where to save logs to
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
