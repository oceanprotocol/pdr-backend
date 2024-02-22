from typing import Tuple

from enforce_typing import enforce_types

from pdr_backend.regressionmodel.regressionmodel_data_factory import (
    RegressionModelDataFactory,
)
from pdr_backend.classifiermodel.classifiermodel_data_factory import (
    ClassifierModelDataFactory,
)
from pdr_backend.regressionmodel.regressionmodel_factory import RegressionModelFactory
from pdr_backend.classifiermodel.classifiermodel_factory import ClassifierModelFactory
from pdr_backend.lake.ohlcv_data_factory import OhlcvDataFactory
from pdr_backend.predictoor.base_predictoor_agent import BasePredictoorAgent
from pdr_backend.util.time_types import UnixTimeS


@enforce_types
class PredictoorAgent3(BasePredictoorAgent):
    def __init__(self, ppss):
        super().__init__(ppss)
        self.get_data_components()

    @enforce_types
    def get_data_components(self):
        ohlcv_data_factory = OhlcvDataFactory(self.ppss.lake_ss)
        mergedohlcv_df = ohlcv_data_factory.get_mergedohlcv_df()
        return mergedohlcv_df

    @enforce_types
    def get_one_sided_prediction(
        self, timestamp: UnixTimeS  # pylint: disable=unused-argument
    ) -> Tuple[bool, float]:
        """
        @description
          Predict for a given timestamp.

        @arguments
          timestamp -- UnixTimeS -- when to make prediction for (unix time)

        @return
          predval -- bool -- if True, it's predicting 'up'. If False, 'down'
          stake -- int -- amount to stake, in units of Eth
        """
        mergedohlcv_df = self.get_data_components()

        model_data_factory = RegressionModelDataFactory(self.ppss.predictoor_ss)
        X, y, _, xrecent = model_data_factory.create_xy(mergedohlcv_df, testshift=0)

        # Compute the model
        regression_model_factory = RegressionModelFactory(
            self.ppss.predictoor_ss.regressionmodel_ss
        )
        model = regression_model_factory.build(X, y)

        # Predict next y
        X_test = xrecent.reshape((1, len(xrecent)))
        predprice = model.predict(X_test)[0]
        curprice = y[-1]
        predval = predprice > curprice

        # Stake amount
        stake = self.ppss.predictoor_ss.stake_amount

        return (bool(predval), stake)

    @enforce_types
    def get_two_sided_prediction(self, timestamp: UnixTimeS) -> Tuple[float, float]:
     """
        @description
          Give a stake for up prediction, and down prediction.

        @arguments
          timestamp -- int -- when to make prediction for (unix time)

        @return
          stake_up -- int -- amount to stake *up*, in units of Eth
          stake_down -- int -- amount to stake *down*, in units of Eth
        """
        mergedohlcv_df = self.get_data_components()

        model_data_factory = ClassifierModelDataFactory(self.ppss.predictoor_ss)
        X, y, _ = model_data_factory.create_xy(mergedohlcv_df, testshift=0)

        # Split X/y into train & test data
        st, fin = 0, X.shape[0] - 1
        X_train, X_test = X[st:fin, :], X[fin : fin + 1]
        y_train_price, y_test_price = y[st:fin], y[fin : fin + 1]  # continuous values
        curprice = y_test_price[-1]
        y_train_class = y_train_price > curprice  # binary values

        # Compute classifier model
        factory = ClassifierModelFactory(self.ppss.predictoor_ss.classifiermodel_ss)
        model = factory.build(X_train, y_train_class)

        # Predict from test data
        y_test_class = model.predict_proba(X_test)
        prob_up = y_test_class[1][0]  # or [0][0] ?
        prob_down = 1.0 - prob_up

        # Stake amount
        stake = self.ppss.predictoor_ss.stake_amount
        stake_up = prob_up * stake
        stake_down = prob_down * stake

        return (stake_up, stake_down)
  