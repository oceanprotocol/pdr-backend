from typing import Tuple

from enforce_typing import enforce_types

from pdr_backend.ppss.predictoor_ss import PredictoorSS
from pdr_backend.binmodel.binmodel_prediction import BinmodelPrediction


class SimPredictoor:
    @enforce_types
    def __init__(self, pdr_ss: PredictoorSS):
        self.pdr_ss = pdr_ss

    @property
    def max_stake_amt(self) -> float:
        return self.pdr_ss.stake_amount.amt_eth

    @enforce_types
    def predict_iter(self, p: BinmodelPrediction) -> Tuple[float, float]:
        """@return (stake_up, stake_down)"""
        if not p.do_trust_models():
            stake_up = 0.0
            stake_down = 0.0
        elif p.prob_UP >= p.prob_DOWN:
            stake_amt = self.max_stake_amt * p.conf_up
            stake_up = stake_amt * p.prob_up_MERGED
            stake_down = stake_amt * (1.0 - p.prob_up_MERGED)
        else:  # p.prob_DOWN > p.prob_UP
            stake_amt = self.max_stake_amt * p.conf_down
            stake_up = stake_amt * p.prob_up_MERGED
            stake_down = stake_amt * (1.0 - p.prob_up_MERGED)

        return (stake_up, stake_down)
