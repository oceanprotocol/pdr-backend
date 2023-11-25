import os
from enforce_typing import enforce_types

from pdr_backend.data_eng.data_ss import DataSS
from pdr_backend.model_eng.model_ss import ModelSS
from pdr_backend.predictoor.base_predictoor_config import BasePredictoorConfig

# To try different strategies, simply change any of the arguments to any
# of the constructors below.
#
# - It does *not* use envvars PAIR_FILTER, TIMEFRAME_FILTER, or SOURCE_FILTER.
#   Why: to avoid ambiguity. Eg is PAIR_FILTER for yval_coin, or input data?


@enforce_types
class PredictoorConfig3(BasePredictoorConfig):
    def __init__(self):
        super().__init__()

        # **Note: the values below are magic numbers. That's ok for now,
        # this is how config files work right now. (Will change with ppss.yaml)
        self.model_ss = ModelSS("LIN")  # LIN, GPR, SVR, NuSVR, LinearSVR

        self.data_ss = DataSS(  # user-controllable params, at data-eng level
            ["binanceus c BTC/USDT,ETH/USDT"],
            csv_dir=os.path.abspath("csvs"),  # eg "csvs". abs or rel loc'n of csvs dir
            st_timestr="2023-01-31",  # eg "2019-09-13_04:00" (earliest), "2019-09-13"
            fin_timestr="now",  #  eg "now", "2023-09-23_17:55", "2023-09-23"
            max_n_train=5000,  # eg 50000. # if inf, only limited by data available
            autoregressive_n=10,  # eg 10. model inputs ar_n past pts z[t-1], .., z[t-ar_n]
        )

        # Note: Inside PredictoorAgent3::get_prediction(),
        #   it's given a yval to predict with {signal, coin, exchange_str}.
        #   If that yval isn't in data_ss input vars {signals, coins, exchanges}
        #   then it will update {signals, coins, exchanges} to include it
