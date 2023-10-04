import os
from typing import Any, List
from enforce_typing import enforce_types
from pdr_backend.models.base_config import BaseConfig

from pdr_backend.models.predictoor_contract import PredictoorContract
from pdr_backend.util.subgraph import query_pending_payouts, wait_till_subgraph_syncs


@enforce_types
def batchify(data: List[Any], batch_size: int):
    return [data[i : i + batch_size] for i in range(0, len(data), batch_size)]


@enforce_types
def request_payout_batches(
    predictoor_contract: PredictoorContract, batch_size: int, timestamps: List[int]
):
    batches = batchify(timestamps, batch_size)
    for batch in batches:
        predictoor_contract.payout_multiple(batch, True)
        print(".", end="", flush=True)
    print("\nBatch completed")


def do_payout():
    config = BaseConfig()
    owner = config.web3_config.owner
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))
    wait_till_subgraph_syncs(config.web3_config, config.subgraph_url)
    pending_payouts = query_pending_payouts(config.subgraph_url, owner)
    total_timestamps = sum(len(timestamps) for timestamps in pending_payouts.values())
    print(f"Found {total_timestamps} slots")

    for contract_address in pending_payouts:
        print(f"Claiming payouts for {contract_address} contract")
        contract = PredictoorContract(config.web3_config, contract_address)
        request_payout_batches(contract, BATCH_SIZE, pending_payouts[contract_address])
