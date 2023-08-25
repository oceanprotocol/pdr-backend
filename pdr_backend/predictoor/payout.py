from typing import List

from pdr_backend.models.predictoor_contract import PredictoorContract
from pdr_backend.util.subgraph import query_pending_payouts


def request_payout(predictoor_contract: PredictoorContract, timestamps: List[int]):
    predictoor_contract.payout_multiple(timestamps, True)


def batchify(data, batch_size):
    return [data[i : i + batch_size] for i in range(0, len(data), batch_size)]


def claim_pending_payouts(predictoor_contract: PredictoorContract, batch_size: int):
    addr = predictoor_contract.config.owner
    pending = query_pending_payouts(addr)
    batches = batchify(pending, batch_size)

    for batch in batches:
        request_payout(predictoor_contract, batch)
