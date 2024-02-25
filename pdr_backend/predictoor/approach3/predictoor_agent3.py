from typing import Tuple

from enforce_typing import enforce_types

from pdr_backend.aimodel.aimodel_data_factory import AimodelDataFactory
from pdr_backend.aimodel.aimodel_factory import AimodelFactory
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
    def get_prediction(
        self, timestamp: UnixTimeS  # pylint: disable=unused-argument
    ) -> Tuple[float, float]:
        """
        @description
          Predict for a given timestamp.

        @arguments
          timestamp -- UnixTimeS -- when to make prediction for (unix time)

        @return
          stake_up -- amt to stake up, in units of Eth
          stake_down -- amt to stake down, ""
        
        @notes
          It uses a classifier to compute confidence in up vs down.
          Here, it allocates stake pro-rata to confidence
          You need to customize this to implement your own strategy.
        """
        mergedohlcv_df = self.get_data_components()

        data_f = AimodelDataFactory(self.ppss.predictoor_ss)
        X, ycont, _, xrecent = data_f.create_xy(mergedohlcv_df, testshift=0)

        curprice = ycont[-1]
        y_thr = curprice
        ybool = data_f.ycont_to_ytrue(ycont, y_thr)

        # build model
        model_f = AimodelFactory(self.ppss.predictoor_ss.aimodel_ss)
        model = model_f.build(X, ybool)

        # predict
        X_test = xrecent.reshape((1, len(xrecent)))
        prob_up = model.predict_ptrue(X_test)[0]

        # stake amounts
        stake_amt = self.ppss.predictoor_ss.stake_amount
        stake_up = prob_up * stake_amt
        stake_down = (1.0 - prob_up) * stake_amt

        return (stake_up, stake_down)
