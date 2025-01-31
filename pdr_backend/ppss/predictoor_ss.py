from typing import List, Optional

from enforce_typing import enforce_types

from pdr_backend.cli.predict_train_feedsets import (
    PredictTrainFeedset,
    PredictTrainFeedsets,
)
from pdr_backend.ppss.aimodel_data_ss import (
    AimodelDataSS,
    aimodel_data_ss_test_dict,
)
from pdr_backend.ppss.aimodel_ss import (
    AimodelSS,
    aimodel_ss_test_dict,
)
from pdr_backend.util.strutil import StrMixin


class PredictoorSS(StrMixin):
    __STR_OBJDIR__ = ["d"]

    @enforce_types
    def __init__(self, d: dict):
        self.d = d
        self.aimodel_data_ss = AimodelDataSS(d["aimodel_data_ss"])
        self.aimodel_ss = AimodelSS(d["aimodel_ss"])

    # ------------------------------------------------------------------
    # yaml properties
    @property
    def predict_train_feedsets(self) -> PredictTrainFeedsets:
        feedset_list: List[dict] = self.d["predict_train_feedsets"]
        return PredictTrainFeedsets.from_list_of_dict(feedset_list)

    # ------------------------------------------------------------------
    # 'predict_train_feedsets' workers
    @enforce_types
    def get_predict_train_feedset(
        self,
        exchange_str: str,
        pair_str: str,
        timeframe_str: str,
    ) -> Optional[PredictTrainFeedset]:
        """Eg return a feedset given ("binance", "BTC/USDT", "5m" """
        return self.predict_train_feedsets.get_feedset(
            exchange_str,
            pair_str,
            timeframe_str,
        )


# =========================================================================
# utilities for testing


@enforce_types
def feedset_test_list() -> list:
    feedset_list = [
        {
            "predict": "binance BTC/USDT c 5m",
            "train_on": "binance BTC/USDT c 5m",
        },
        {
            "predict": "kraken ETH/USDT c 5m",
            "train_on": "kraken ETH/USDT c 5m",
        },
    ]
    return feedset_list


@enforce_types
def predictoor_ss_test_dict(
    feedset_list: Optional[List] = None,
    aimodel_data_ss_dict: Optional[dict] = None,
    aimodel_ss_dict: Optional[dict] = None,
) -> dict:
    """Use this function's return dict 'd' to construct PredictoorSS(d)"""
    feedset_list = feedset_list or feedset_test_list()
    d = {
        "predict_train_feedsets": feedset_list,
        "aimodel_data_ss": aimodel_data_ss_dict or aimodel_data_ss_test_dict(),
        "aimodel_ss": aimodel_ss_dict or aimodel_ss_test_dict(),
    }
    return d
