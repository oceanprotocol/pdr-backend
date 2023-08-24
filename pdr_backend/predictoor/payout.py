from typing import List

from pdr_backend.models.predictoor_contract import PredictoorContract

def request_payout(predictoor_contract: PredictoorContract, timestamps: List[int]):
    predictoor_contract.payout_multiple(timestamps, True)
