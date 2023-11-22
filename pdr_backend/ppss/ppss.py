import os
from typing import Optional

import yaml
from pdr_backend.dfbuyer.dfbuyer_ss import DFBuyerSS

from pdr_backend.ppss.data_pp import DataPP
from pdr_backend.ppss.data_ss import DataSS
from pdr_backend.ppss.model_ss import ModelSS
from pdr_backend.ppss.predictoor_ss import PredictoorSS
from pdr_backend.ppss.sim_ss import SimSS
from pdr_backend.ppss.trader_pp import TraderPP
from pdr_backend.ppss.trader_ss import TraderSS
from pdr_backend.ppss.web3_pp import Web3PP
from pdr_backend.trueval.trueval_ss import TruevalSS


class PPSS:  # pylint: disable=too-many-instance-attributes
    """
    All uncontrollable (pp) and controllable (ss) settings in one place
    Constructed by loading from a .yaml file or yaml-formatted string.
    """

    def __init__(
        self,
        network: str,  # e.g. "sapphire-testnet"
        yaml_filename: Optional[str] = None,
        yaml_str: Optional[str] = None,
    ):
        # preconditions
        assert (
            yaml_filename or yaml_str and not (yaml_filename and yaml_str)
        ), "need to set yaml_filename_ or yaml_str but not both"

        # get d
        if yaml_filename is not None:
            with open(yaml_filename, "r") as f:
                d = yaml.safe_load(f)
        else:
            d = yaml.safe_load(str(yaml_str))

        # fill attributes from d
        self.web3_pp = Web3PP(network, d["web3_pp"])
        self.data_pp = DataPP(d["data_pp"])
        self.data_ss = DataSS(d["data_ss"])
        self.model_ss = ModelSS(d["model_ss"])
        self.predictoor_ss = PredictoorSS(d["predictoor_ss"])
        self.trader_pp = TraderPP(d["trader_pp"])
        self.trader_ss = TraderSS(d["trader_ss"])
        self.sim_ss = SimSS(d["sim_ss"])
        self.trueval_ss = TruevalSS(d["trueval_ss"])
        self.dfbuyer_ss = DFBuyerSS(d["dfbuyer_ss"])

    def __str__(self):
        s = ""
        s += f"web3_pp={self.web3_pp}\n"
        s += f"data_pp={self.data_pp}\n"
        s += f"data_ss={self.data_ss}\n"
        s += f"model_ss={self.model_ss}\n"
        s += f"predictoor_ss={self.predictoor_ss}\n"
        s += f"trader_pp={self.trader_pp}\n"
        s += f"trader_ss={self.trader_ss}\n"
        s += f"sim_ss={self.sim_ss}\n"
        s += f"trueval_ss={self.trueval_ss}\n"
        return s

_CACHED_FILE_S = None
def fast_test_yaml_str(tmpdir):
    """Use this for testing. It has fast runtime."""
    with open("./ppss.yaml") as f:
        s = f.read()

    if CACHED_PPSS is None:
        s = CACHED_PPSS
        
    assert "csv_dir: csvs" in s
    s = s.replace("csv_dir: csvs", f"csv_dir: {os.path.join(tmpdir, 'csvs')}")
    
    assert "log_dir: logs" in s
    s.replace("log_dir: logs", f"log_dir: {os.path.join(tmpdir, 'logs')}")

    return s
