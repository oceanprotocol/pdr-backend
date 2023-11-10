import os
from typing import Tuple

from typing import Dict, List, Tuple, Union

from enforce_typing import enforce_types
from pdr_backend.simulation.data_factory import DataFactory
from pdr_backend.simulation.model_factory import ModelFactory
from pdr_backend.simulation.model_ss import ModelSS

from pdr_backend.predictoor.base_predictoor_agent import BasePredictoorAgent
from pdr_backend.predictoor.approach4.predictoor_config4 import PredictoorConfig4
from pdr_backend.simulation.timeutil import timestr_to_ut
from pdr_backend.simulation.data_ss import DataSS

from enforce_typing import enforce_types
from sklearn.linear_model import LinearRegression
from sklearn.svm import SVR, NuSVR, LinearSVR
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF

from pdr_backend.simulation.prev_model import PrevModel 
from pdr_backend.simulation.model_ss import ModelSS

from datetime import datetime
import numpy as np

@enforce_types
class PredictoorAgent4(BasePredictoorAgent):
    predictoor_config_class = PredictoorConfig4

    def __init__(self, config: PredictoorConfig4):
        super().__init__(config)
        self.config: PredictoorConfig4 = config

        # Set SS
        self.data_ss: Dict[str, DataSS] = {}
        self.model_ss = ModelSS(
            self.config.model_ss
        )  # PREV, LIN, GPR, SVR, NuSVR, LinearSVR       
        self.model: Dict[str, Union[
            PrevModel,
            LinearRegression, 
            GaussianProcessRegressor, 
            SVR, 
            NuSVR, 
            LinearSVR
        ]] = {}

        self.X_test: Dict[str, np.array] = {}
        self.y_train: Dict[str, np.array] = {}

        for addr in self.feeds.keys():
            self.build_model(addr)

    def build_model(self, addr: str):
        print(f"Building model for: {addr} started: {datetime.now().timestamp()}")
        
        coins = ["ETH", "BTC"]
        signals = self.config.signals
        exchange_ids = self.config.exchange_ids

        # Uncontrollable data_ss params
        feed = self.feeds[addr]
        timeframe = feed.timeframe  # eg 5m, 1h
        yval_coin = feed.base  # eg ETH
        usdcoin = feed.quote  # eg USDT
        yval_exchange_id = feed.source
        yval_signal = "close"

        if yval_coin not in coins:  # eg DOT
            coins.append(yval_coin)
        if yval_exchange_id not in exchange_ids:
            exchange_ids.append(yval_exchange_id)

        # Set data_ss
        data_ss = DataSS(
            csv_dir=os.path.abspath("csvs"),
            st_timestamp=self.config.st_timestamp,
            fin_timestamp=timestr_to_ut("now"),
            max_N_train=self.config.max_N_train,
            N_test=self.config.N_test,
            Nt=self.config.Nt,
            usdcoin=usdcoin,
            timeframe=timeframe,
            signals=signals,
            coins=coins,
            exchange_ids=exchange_ids,
            yval_exchange_id=yval_exchange_id,
            yval_coin=yval_coin,
            yval_signal=yval_signal,
        )
        self.data_ss[addr] = data_ss

        data_factory = DataFactory(data_ss)

        # Compute X/y
        hist_df = data_factory.get_hist_df()
        X, y, _, _ = data_factory.create_xy(hist_df, testshift=0)

        # Split X/y
        st, fin = 0, X.shape[0] - 1
        X_train, self.X_test[addr] = X[st:fin, :], X[fin : fin + 1]
        self.y_train[addr], _ = y[st:fin], y[fin : fin + 1]

        # Compute the model
        model_factory = ModelFactory(self.model_ss)
        model = model_factory.build(X_train, self.y_train[addr])
        self.model[addr] = model

        print(f"Finished building model for: {addr} ended: {datetime.now().timestamp()}")

    def get_prediction(
        self, addr: str, timestamp: int  # pylint: disable=unused-argument
    ) -> Tuple[bool, float]:
        """
        @description
          Given a feed, let's predict for a given timestamp.

        @arguments
          addr -- str -- address of the trading pair. Info in self.feeds[addr]
          timestamp -- int -- when to make prediction for (unix time)

        @return
          predval -- bool -- if True, it's predicting 'up'. If False, 'down'
          stake -- int -- amount to stake, in units of Eth
        """
        # Predict
        predprice = self.model[addr].predict(self.X_test[addr])[0]
        curprice = self.y_train[addr][-1]
        predval = predprice > curprice

        # Stake what was set via envvar STAKE_AMOUNT
        stake = self.config.stake_amount

        return (bool(predval), stake)

    def _process_block_at_feed(self, addr: str, timestamp: int) -> tuple:
        """Returns (predval, stake, submitted)"""
        # base data
        _, contract = self.feeds[addr], self.contracts[addr]
        epoch = contract.get_current_epoch()
        
        # already predicted for?
        if (
            self.prev_submit_epochs_per_feed.get(addr)
            and epoch == self.prev_submit_epochs_per_feed[addr][-1]
        ):
            print("      Done feed: already predicted this epoch")
            return (None, None, False)
        
        super()._process_block_at_feed(addr, timestamp)