import os

import yaml

from pdr_backend.data_eng.data_pp import DataPP
from pdr_backend.data_eng.data_ss import DataSS
from pdr_backend.data_eng.model_ss import ModelSS
from pdr_backend.data_eng.sim_ss import SimSS
from pdr_backend.data_eng.trade_pp import TradePP
from pdr_backend.data_eng.trade_ss import TradeSS

class PPSS:
    """
    All uncontrollable (pp) and controllable (ss) settings in one place
    Constructed by loading from a .yaml file.
    """
    
    def __init__(self, yaml_filename: str):
        with open(yaml_filename, 'r') as file:
            d = yaml.safe_load(file)
        
        self.data_pp = DataPP(
            d["data_pp"]["timeframe"],
            d["data_pp"]["predict_feed"],
            d["data_pp"]["test_n"],
        )

        self.data_ss = DataSS(
            d["data_ss"]["input_feeds"],
            os.path.abspath(d["data_ss"]["csv_dir"]),
            d["data_ss"]["st_timestr"],
            d["data_ss"]["fin_timestr"],
            d["data_ss"]["max_n_train"],
            d["data_ss"]["autoregressive_n"],
        )

        self.model_ss = ModelSS(
            d["model_ss"]["approach"],
        )

        self.trade_pp = TradePP(
            d["trade_pp"]["fee_percent"],
            d["trade_pp"]["init_holdings"],
        )

        self.trade_ss = TradeSS(
            d["trade_ss"]["buy_amt"],
        )

        self.sim_ss = SimSS(  # user-controllable params, at sim level
            d["sim_ss"]["do_plot"],
            os.path.abspath("./"),
        )

    def __str__(self):
        s = ""
        s += f"data_pp={data_pp}\n"
        s += f"data_ss={data_ss}\n"
        s += f"model_ss={model_ss}\n"
        s += f"trade_pp={trade_pp}\n"
        s += f"trade_ss={trade_ss}\n"
        s += f"sim_ss={sim_ss}\n"
        return s
