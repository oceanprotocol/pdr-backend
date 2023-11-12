from enforce_typing import enforce_types

from pdr_backend.util.timeutil import timestr_to_ut
from pdr_backend.model_eng.model_ss import ModelSS
from pdr_backend.predictoor.base_predictoor_config import BasePredictoorConfig


@enforce_types
class PredictoorConfig3(BasePredictoorConfig):
    def __init__(self):
        super().__init__()
        
        self.data_ss = DataSS(  # user-controllable params, at data-eng level
            csv_dir=os.path.abspath("csvs"), # eg "csvs". abs or rel loc'n of csvs dir
            st_timestamp=timestr_to_ut("2023-01-31"),  # "2019-09-13_04:00" is earliest
            fin_timestamp=timestr_to_ut("now"),  # eg 'now','2023-06-21_17:55'
            max_N_train=5000,  # eg 50000. # if inf, only limited by data available
            Nt=10,  # eg 10. model inputs Nt past pts z[t-1], .., z[t-Nt]
            signals=["close"],  # for model input vars. eg ["open","high","volume"] 
            coins=["BTC", "ETH"] # for model input vars. eg ["ETH", "BTC"]
            exchange_ids=["binance"], # for model input vars. eg ["binance", "mxc"]
        )

        self.model_ss = ModelSS("LIN")  # LIN, GPR, SVR, NuSVR, LinearSVR
