import os
import time
from typing import Any, List
from enforce_typing import enforce_types
from pdr_backend.models.base_config import BaseConfig

from pdr_backend.models.predictoor_contract import PredictoorContract
from pdr_backend.util.subgraph import query_pending_payouts, wait_until_subgraph_syncs
from pdr_backend.models.dfrewards import DFRewards


@enforce_types
def batchify(data: List[Any], batch_size: int):
    return [data[i : i + batch_size] for i in range(0, len(data), batch_size)]


@enforce_types
def request_payout_batches(
    predictoor_contract: PredictoorContract, batch_size: int, timestamps: List[int]
):
    batches = batchify(timestamps, batch_size)
    for batch in batches:
        retries = 0
        success = False

        while retries < 5 and not success:
            try:
                predictoor_contract.payout_multiple(batch, True)
                print(".", end="", flush=True)
                success = True
            except Exception as e:
                retries += 1
                print(f"Error: {e}. Retrying... {retries}/5", flush=True)
                time.sleep(1)

        if not success:
            print("\nFailed after 5 attempts. Moving to next batch.", flush=True)

    print("\nBatch completed")


def do_payout():
    config = BaseConfig()
    owner = config.web3_config.owner
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", "250"))
    print("Starting payout")
    wait_until_subgraph_syncs(config.web3_config, config.subgraph_url)
    print("Finding pending payouts")
    pending_payouts = query_pending_payouts(config.subgraph_url, owner)
    total_timestamps = sum(len(timestamps) for timestamps in pending_payouts.values())
    print(f"Found {total_timestamps} slots")

    for contract_address in pending_payouts:
        print(f"Claiming payouts for {contract_address}")
        contract = PredictoorContract(config.web3_config, contract_address)
        request_payout_batches(contract, BATCH_SIZE, pending_payouts[contract_address])


def do_rose_payout():
    address = "0xc37F8341Ac6e4a94538302bCd4d49Cf0852D30C0"
    wrapped_rose = "0x8Bc2B030b299964eEfb5e1e0b36991352E56D2D3"
    config = BaseConfig()
    owner = config.web3_config.owner
    if config.web3_config.w3.eth.chain_id != 23294:
        raise Exception("Unsupported network")
    contract = DFRewards(config.web3_config, address)
    claimable_rewards = contract.get_claimable_rewards(owner, wrapped_rose)
    print(f"Found {claimable_rewards} ROSE available to claim")

    if claimable_rewards > 0:
        print("Claiming ROSE rewards...")
        contract.claim_rewards(owner, wrapped_rose)
    else:
        print("No rewards, exiting")

    print("ROSE reward claim done")
