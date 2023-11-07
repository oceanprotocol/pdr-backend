import os
from typing import Tuple

from enforce_typing import enforce_types
from pdr_backend.simulation.data_factory import DataFactory
from pdr_backend.simulation.model_factory import ModelFactory
from pdr_backend.simulation.model_ss import ModelSS

from pdr_backend.predictoor.base_predictoor_agent import BasePredictoorAgent
from pdr_backend.predictoor.approach3.predictoor_config3 import PredictoorConfig3
from pdr_backend.simulation.timeutil import timestr_to_ut
from pdr_backend.simulation.data_ss import DataSS


@enforce_types
class PredictoorAgent3(BasePredictoorAgent):
    predictoor_config_class = PredictoorConfig3

    def __init__(self, config: PredictoorConfig3):
        super().__init__(config)
        self.config: PredictoorConfig3 = config

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
        # Set model_ss
        model_ss = ModelSS(
            self.config.model_ss
        )  # PREV, LIN, GPR, SVR, NuSVR, LinearSVR

        # Controllable data_ss params. Hardcoded; could be moved to envvars

        coins = ["ETH", "BTC"]
        signals = ["close"]  # ["open", "high","low", "close", "volume"]
        exchange_ids = ["binanceus"]  # ["binance", "kraken"]

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

        data_factory = DataFactory(data_ss)

        # Compute X/y
        hist_df = data_factory.get_hist_df()
        X, y, _, _ = data_factory.create_xy(hist_df, testshift=0)

        # Split X/y
        st, fin = 0, X.shape[0] - 1
        X_train, X_test = X[st:fin, :], X[fin : fin + 1]
        y_train, _ = y[st:fin], y[fin : fin + 1]

        # Compute the model
        model_factory = ModelFactory(model_ss)
        model = model_factory.build(X_train, y_train)

        # Predict
        predprice = model.predict(X_test)[0]
        curprice = y_train[-1]
        predval = predprice > curprice

        # Stake what was set via envvar STAKE_AMOUNT
        stake = self.config.stake_amount

        return (bool(predval), stake)
