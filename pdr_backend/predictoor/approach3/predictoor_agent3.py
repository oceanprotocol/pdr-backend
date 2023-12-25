import copy
from typing import Tuple

from enforce_typing import enforce_types

import pandas as pd
from pdr_backend.aimodel.aimodel_data_factory import AimodelDataFactory
from pdr_backend.aimodel.aimodel_factory import AimodelFactory
from pdr_backend.lake.ohlcv_data_factory import OhlcvDataFactory
from pdr_backend.ppss.data_pp import DataPP
from pdr_backend.ppss.data_ss import DataSS
from pdr_backend.predictoor.base_predictoor_agent import BasePredictoorAgent


@enforce_types
class PredictoorAgent3(BasePredictoorAgent):
    # override init
    # initialize the OhlcvDataFactory
    def __init__(self, ppss):
        super().__init__(ppss)

        self.get_data_components()
    
    def get_data_components(self) -> Tuple[DataPP, DataSS, pd.DataFrame]:
        feed = self.feed
        d = copy.deepcopy(self.ppss.data_pp.d)
        d["predict_feeds"] = [f"{feed.source} {feed.pair} c"]
        data_pp = DataPP(d)
        data_ss = self.ppss.data_ss.copy_with_yval(data_pp)

        ohlcv_data_factory = OhlcvDataFactory(data_pp, data_ss)
        mergedohlcv_df = ohlcv_data_factory.get_mergedohlcv_df()

        return data_pp, data_ss, mergedohlcv_df

    def get_prediction(
        self, timestamp: int  # pylint: disable=unused-argument
    ) -> Tuple[bool, float]:
        """
        @description
          Predict for a given timestamp.

        @arguments
          timestamp -- int -- when to make prediction for (unix time)

        @return
          predval -- bool -- if True, it's predicting 'up'. If False, 'down'
          stake -- int -- amount to stake, in units of Eth
        """
        # Get data_pp, data_ss, mergedohlcv_df
        data_pp, data_ss, mergedohlcv_df = self.get_data_components()

        # From data_ss, build X/y
        model_data_factory = AimodelDataFactory(data_pp, data_ss)
        X, y, _ = model_data_factory.create_xy(mergedohlcv_df, testshift=0)

        # Split X/y into train & test data
        st, fin = 0, X.shape[0] - 1
        X_train, X_test = X[st:fin, :], X[fin : fin + 1]
        y_train, _ = y[st:fin], y[fin : fin + 1]

        # Compute the model from train data
        aimodel_factory = AimodelFactory(self.ppss.aimodel_ss)
        model = aimodel_factory.build(X_train, y_train)

        # Predict from test data
        predprice = model.predict(X_test)[0]
        curprice = y_train[-1]
        predval = predprice > curprice

        # Stake amount
        stake = self.ppss.predictoor_ss.stake_amount

        return (bool(predval), stake)
