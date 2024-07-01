from enforce_typing import enforce_types
import numpy as np
import polars as pl

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_feeds import ArgFeeds
from pdr_backend.aimodel.aimodel_data_factory import AimodelDataFactory
from pdr_backend.cli.predict_train_feedset import PredictTrainFeedset
from pdr_backend.ppss.aimodel_data_ss import AimodelDataSS
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.ppss.predictoor_ss import PredictoorSS
from pdr_backend.sim.sim_model_data import SimModelData, SimModelData1Dir

class SimModelDataFactory:
    @enforce_types
    def __init__(self, ppss: PPSS, predict_train_feedset: PredictTrainFeedset):
        self.ppss = ppss
        self.predict_train_feedset = predict_train_feedset

    @property
    def pdr_ss(self) -> PredictoorSS:
        return self.ppss.predictoor_ss

    @property
    def aimodel_data_ss(self) -> AimodelDataSS:
        return self.pdr_ss.aimodel_data_ss
    
    @property
    def class_thr(self) -> float:
        return self.aimodel_data_ss.class_thr

    @enforce_types
    def testshift(self, test_i: int) -> int:
        test_n = self.ppss.sim_ss.test_n
        return AimodelDataFactory.testshift(test_n, test_i)

    @enforce_types
    def build(self, test_i: int, mergedohlcv_df: pl.DataFrame) -> SimModelData:
        """Construct sim model data"""
        df = mergedohlcv_df
        testshift = self.testshift(test_i) # eg [99, 98, .., 2, 1, 0]
        data_f = AimodelDataFactory(self.pdr_ss)

        p: ArgFeed = self.predict_train_feedset.predict
        _, _, y_close, _, _ = data_f.create_xy(
            df, testshift, p.variant_close(), ArgFeeds([p.variant_close()]),
        )
        X_high, _, y_high, _, _ = data_f.create_xy(
            df, testshift, p.variant_high(), ArgFeeds([p.variant_high()]),
        )
        X_low, _, y_low, _, _ = data_f.create_xy(
            df, testshift, p.variant_low(), ArgFeeds([p.variant_low()]),
        )

        ytrue_UP = []
        ytrue_DOWN = []
        for i, cur_close in enumerate(y_close[:-1]):
            # did the next high value go above the current close+% value?
            next_high = y_high[i+1]
            thr_UP = self.thr_UP(cur_close)
            ytrue_UP.append(next_high > thr_UP)
            
            # did the next low value go below the current close-% value?
            next_low = y_low[i+1]
            thr_DOWN = self.thr_DOWN(cur_close)
            ytrue_DOWN.append(next_low < thr_DOWN)        

        ytrue_UP, ytrue_DOWN = np.array(ytrue_UP), np.array(ytrue_DOWN)
        d_UP = SimModelData1Dir(X_high[1:,:], ytrue_UP) # or is it [:-1,:]
        d_DOWN = SimModelData1Dir(X_low[1:,:], ytrue_DOWN) # ""
        # note: alternatively, each input X could be h+l+c rather than just h or l
        d = SimModelData(d_UP, d_DOWN)
        
        return d

    @enforce_types
    def thr_UP(self, cur_close: float) -> float:
        return cur_close * (1 + self.class_thr)
    
    @enforce_types
    def thr_DOWN(self, cur_close: float) -> float:
        return cur_close * (1 - self.class_thr)    
        
        
