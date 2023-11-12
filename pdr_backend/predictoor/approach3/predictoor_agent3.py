from typing import Tuple

from enforce_typing import enforce_types

from pdr_backend.data_eng.data_factory import DataFactory
from pdr_backend.data_eng.data_pp import DataPP
from pdr_backend.model_eng.model_factory import ModelFactory

from pdr_backend.predictoor.base_predictoor_agent import BasePredictoorAgent
from pdr_backend.predictoor.approach3.predictoor_config3 import PredictoorConfig3
from pdr_backend.util.timeutil import timestr_to_ut


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
        feed = self.feeds[addr]

        # user-uncontrollable params, at data-eng level
        data_pp = DataPP(
            timeframe=feed.timeframe,  # eg "5m"
            yval_exchange_id=feed.source,  # eg "binance"
            yval_coin=feed.base,  # eg "BTC"
            usdcoin=feed.quote,  # eg "USDT"
            yval_signal="close",  # pdr feed setup is always "close"
            N_test=1,  # N/A for this context
        )

        # user-controllable params, at data-eng level
        data_ss = self.config.data_ss.copy_with_yval(data_pp)
        data_ss.fin_timestamp = timestr_to_ut("now")

        #  user-controllable params, at model-eng level
        model_ss = self.config.model_ss

        # do work...
        data_factory = DataFactory(data_pp, data_ss)

        # Compute X/y
        hist_df = data_factory.get_hist_df()
        X, y, _ = data_factory.create_xy(hist_df, testshift=0)

        # Split X/y into train & test data
        st, fin = 0, X.shape[0] - 1
        X_train, X_test = X[st:fin, :], X[fin : fin + 1]
        y_train, _ = y[st:fin], y[fin : fin + 1]

        # Compute the model from train data
        model_factory = ModelFactory(model_ss)
        model = model_factory.build(X_train, y_train)

        # Predict from test data
        predprice = model.predict(X_test)[0]
        curprice = y_train[-1]
        predval = predprice > curprice

        # Stake what was set via envvar STAKE_AMOUNT
        stake = self.config.stake_amount

        return (bool(predval), stake)
