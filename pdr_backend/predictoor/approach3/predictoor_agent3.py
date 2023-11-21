import copy
from typing import Tuple

from enforce_typing import enforce_types

from pdr_backend.data_eng.data_factory import DataFactory
from pdr_backend.ppss.data_pp import DataPP
from pdr_backend.data_eng.model_factory import ModelFactory
from pdr_backend.predictoor.base_predictoor_agent import BasePredictoorAgent


@enforce_types
class PredictoorAgent3(BasePredictoorAgent):
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
        # Compute data_ss
        feed = self.feeds[addr]
        d = copy.deepcopy(self.ppss.data_pp.d)
        d["predict_feeds"] = [f"{feed.source} c {feed.pair}"]
        data_pp = DataPP(d)
        data_ss = self.ppss.data_ss.copy_with_yval(data_pp)

        # From data_ss, build X/y
        data_factory = DataFactory(data_pp, data_ss)
        hist_df = data_factory.get_hist_df()
        X, y, _ = data_factory.create_xy(hist_df, testshift=0)

        # Split X/y into train & test data
        st, fin = 0, X.shape[0] - 1
        X_train, X_test = X[st:fin, :], X[fin : fin + 1]
        y_train, _ = y[st:fin], y[fin : fin + 1]

        # Compute the model from train data
        model_factory = ModelFactory(self.ppss.model_ss)
        model = model_factory.build(X_train, y_train)

        # Predict from test data
        predprice = model.predict(X_test)[0]
        curprice = y_train[-1]
        predval = predprice > curprice

        # Stake amount
        stake = self.ppss.predictoor_ss.stake_amount

        return (bool(predval), stake)
