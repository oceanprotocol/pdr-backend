import os

import yaml

from pdr_backend.data_eng.data_pp import DataPP
from pdr_backend.data_eng.data_ss import DataSS
from pdr_backend.data_eng.model_ss import ModelSS
from pdr_backend.data_eng.predictoor_ss import PredictoorSS
from pdr_backend.data_eng.sim_ss import SimSS
from pdr_backend.data_eng.trader_pp import TraderPP
from pdr_backend.data_eng.trader_ss import TraderSS

class PPSS:
    """
    All uncontrollable (pp) and controllable (ss) settings in one place
    Constructed by loading from a .yaml file or yaml-formatted string.
    """
    
    def __init__(
            self,
            yaml_filename:Optional[str]=None,
            yaml_str:Optional[str]=None,
    ):
        # preconditions
        assert yaml_filename or yaml_str and not (yaml_filename and yaml_str),\
            "need to set yaml_filename_ or yaml_str but not both"

        # get d
        if yaml_filename is not None:
            with open(yaml_filename, 'r') as f:
                d = yaml.safe_load(f)
        else:
            d = yaml.safe_load(yaml_str)
            
        # fill attributes from d
        self.data_pp = DataPP(d["data_pp"])
        self.data_ss = DataSS(d["data_ss"])
        self.model_ss = ModelSS(d["model_ss"])
        self.predictoor_ss = PredictoorSS(d["predictoor_ss"])
        self.trader_pp = TraderPP(d["trader_pp"])
        self.trader_ss = TraderSS(d["trader_ss"])
        self.sim_ss = SimSS(d["sim_ss"])

    def __str__(self):
        s = ""
        s += f"data_pp={self.data_pp}\n"
        s += f"data_ss={self.data_ss}\n"
        s += f"model_ss={self.model_ss}\n"
        s += f"predictoor_ss={self.predictoor_ss}\n"
        s += f"trader_pp={self.trader_pp}\n"
        s += f"trader_ss={self.trader_ss}\n"
        s += f"sim_ss={self.sim_ss}\n"
        return s

def fast_test_yaml_str(tmpdir):
    """Use this for testing. It has fast runtime."""
    csv_dir = os.path.join(tmpdir, "csvs")
    log_dir = os.path.join(tmpdir, "logs")
    return f"""data_pp:
timeframe: 5m
predict_feeds:
  - binance c BTC/USDT
sim_only:
  test_n : 100

data_ss:
  input_feeds :
    - binance oc BTC/USDT,ETH/USDT
  st_timestr: 2023-06-22_00:00
  fin_timestr: 2023-06-24_00:00
  max_n_train: 500
  autoregressive_n : 2
  csv_dir: {csv_dir}

model_ss:
  approach: LIN

predictoor_ss:
  bot_only:
    s_until_epoch_end: 60
    stake_amount: 1
  approach3:

trader_pp:
  sim_only:
    fee_percent: 0.0
    init_holdings:
      - 100000 USDT
      - 0 BTC

trader_ss:
  sim_only:
    buy_amt: 10000 USDT

sim_ss:
  do_plot: False
  log_dir: {log_dir}
    """
