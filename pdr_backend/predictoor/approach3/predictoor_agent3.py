from typing import Tuple

from enforce_typing import enforce_types
import numpy as np

from pdr_backend.aimodel.aimodel_data_factory import AimodelDataFactory
from pdr_backend.aimodel.aimodel_factory import AimodelFactory
from pdr_backend.lake.ohlcv_data_factory import OhlcvDataFactory
from pdr_backend.predictoor.base_predictoor_agent import BasePredictoorAgent


@enforce_types
class PredictoorAgent3(BasePredictoorAgent):
    def __init__(self, ppss):
        super().__init__(ppss)
        self.get_data_components()

    @enforce_types
    def get_data_components(self):
        pq_data_factory = OhlcvDataFactory(self.ppss.lake_ss)
        mergedohlcv_df = pq_data_factory.get_mergedohlcv_df()
        return mergedohlcv_df

    @enforce_types
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
        mergedohlcv_df = self.get_data_components()

        model_data_factory = AimodelDataFactory(self.ppss.predictoor_ss)
        X, y, _ = model_data_factory.create_xy(mergedohlcv_df, testshift=0)

        # Compute the model
        aimodel_factory = AimodelFactory(self.ppss.predictoor_ss.aimodel_ss)
        model = aimodel_factory.build(X, y)

        # Predict next y
        n_vars = X.shape[1]
        X_test = np.empty((1, n_vars), dtype=float)
        X_test[0, :] = y[-n_vars:]

        predprice = model.predict(X_test)[0]
        curprice = y[-1]
        predval = predprice > curprice

        # Stake amount
        stake = self.ppss.predictoor_ss.stake_amount

        return (bool(predval), stake)
