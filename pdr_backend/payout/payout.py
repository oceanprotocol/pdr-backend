import time
from typing import Any, List
from enforce_typing import enforce_types

from pdr_backend.models.dfrewards import DFRewards
from pdr_backend.models.predictoor_contract import PredictoorContract
from pdr_backend.models.wrapped_token import WrappedToken
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.util.constants import SAPPHIRE_MAINNET_CHAINID
from pdr_backend.util.subgraph import query_pending_payouts, wait_until_subgraph_syncs


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


@enforce_types
def do_ocean_payout(ppss: PPSS):
    web3_config = ppss.web3_pp.web3_config
    subgraph_url: str = ppss.web3_pp.subgraph_url

    assert ppss.web3_pp.network == "sapphire-mainnet"
    assert web3_config.w3.eth.chain_id == SAPPHIRE_MAINNET_CHAINID

    print("Starting payout")
    wait_until_subgraph_syncs(web3_config, subgraph_url)
    print("Finding pending payouts")
    pending_payouts = query_pending_payouts(subgraph_url, web3_config.owner)
    total_timestamps = sum(len(timestamps) for timestamps in pending_payouts.values())
    print(f"Found {total_timestamps} slots")

    for pdr_contract_addr in pending_payouts:
        print(f"Claiming payouts for {pdr_contract_addr}")
        pdr_contract = PredictoorContract(web3_config, pdr_contract_addr)
        request_payout_batches(
            pdr_contract, ppss.payout_ss.batch_size, pending_payouts[pdr_contract_addr]
        )


@enforce_types
def do_rose_payout(ppss: PPSS):
    web3_config = ppss.web3_pp.web3_config

    assert ppss.web3_pp.network == "sapphire-mainnet"
    assert web3_config.w3.eth.chain_id == SAPPHIRE_MAINNET_CHAINID

    dfrewards_addr = "0xc37F8341Ac6e4a94538302bCd4d49Cf0852D30C0"
    wROSE_addr = "0x8Bc2B030b299964eEfb5e1e0b36991352E56D2D3"

    dfrewards_contract = DFRewards(web3_config, dfrewards_addr)
    claimable_rewards = dfrewards_contract.get_claimable_rewards(
        web3_config.owner, wROSE_addr
    )
    print(f"Found {claimable_rewards} wROSE available to claim")

    if claimable_rewards > 0:
        print("Claiming wROSE rewards...")
        dfrewards_contract.claim_rewards(web3_config.owner, wROSE_addr)
    else:
        print("No rewards available to claim")

    print("Converting wROSE to ROSE")
    time.sleep(10)
    wROSE = WrappedToken(web3_config, wROSE_addr)
    wROSE_bal = wROSE.balanceOf(web3_config.owner)
    if wROSE_bal == 0:
        print("wROSE balance is 0")
    else:
        print(f"Found {wROSE_bal/1e18} wROSE, converting to ROSE...")
        wROSE.withdraw(wROSE_bal)

    print("ROSE reward claim done")
