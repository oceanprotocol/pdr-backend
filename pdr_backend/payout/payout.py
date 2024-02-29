import logging
import time
from typing import Any, List

from enforce_typing import enforce_types

from pdr_backend.contract.dfrewards import DFRewards
from pdr_backend.contract.predictoor_contract import PredictoorContract
from pdr_backend.contract.wrapped_token import WrappedToken
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.subgraph.subgraph_pending_payouts import query_pending_payouts
from pdr_backend.subgraph.subgraph_sync import wait_until_subgraph_syncs
from pdr_backend.util.constants import SAPPHIRE_MAINNET_CHAINID

logger = logging.getLogger("payout")


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

        print(".", end="", flush=True)

        while retries < 5 and not success:
            try:
                wait_for_receipt = True
                predictoor_contract.payout_multiple(batch, wait_for_receipt)
                success = True
            except Exception as e:
                retries += 1
                logger.warning("Error: %s. Retrying... %d/5", e, retries)
                time.sleep(1)

        if not success:
            logger.error("Failed after 5 attempts. Moving to next batch.")

    logger.info("Batch completed")


@enforce_types
def do_ocean_payout(ppss: PPSS, check_network: bool = True):
    web3_config = ppss.web3_pp.web3_config
    subgraph_url: str = ppss.web3_pp.subgraph_url

    if check_network:
        assert ppss.web3_pp.network == "sapphire-mainnet"
        assert web3_config.w3.eth.chain_id == SAPPHIRE_MAINNET_CHAINID

    logger.info("Starting payout")
    wait_until_subgraph_syncs(web3_config, subgraph_url)
    logger.info("Finding pending payouts")
    pending_payouts = query_pending_payouts(subgraph_url, web3_config.owner)
    total_timestamps = sum(len(timestamps) for timestamps in pending_payouts.values())
    logger.info("Found %d slots", total_timestamps)

    for pdr_contract_addr in pending_payouts:
        logger.info("Claiming payouts for %s", pdr_contract_addr)
        pdr_contract = PredictoorContract(ppss.web3_pp, pdr_contract_addr)
        request_payout_batches(
            pdr_contract, ppss.payout_ss.batch_size, pending_payouts[pdr_contract_addr]
        )

    logger.info("Payout done")


@enforce_types
def do_rose_payout(ppss: PPSS, check_network: bool = True):
    web3_config = ppss.web3_pp.web3_config

    if check_network:
        assert ppss.web3_pp.network == "sapphire-mainnet"
        assert web3_config.w3.eth.chain_id == SAPPHIRE_MAINNET_CHAINID

    dfrewards_addr = "0xc37F8341Ac6e4a94538302bCd4d49Cf0852D30C0"
    wROSE_addr = "0x8Bc2B030b299964eEfb5e1e0b36991352E56D2D3"

    dfrewards_contract = DFRewards(ppss.web3_pp, dfrewards_addr)
    claimable_rewards = dfrewards_contract.get_claimable_rewards(
        web3_config.owner, wROSE_addr
    )
    logger.info("Found %s wROSE available to claim", claimable_rewards.amt_eth)

    if claimable_rewards > 0:
        logger.info("Claiming wROSE rewards...")
        dfrewards_contract.claim_rewards(web3_config.owner, wROSE_addr)
    else:
        logger.warning("No rewards available to claim")

    logger.info("Converting wROSE to ROSE")
    time.sleep(10)
    wROSE = WrappedToken(ppss.web3_pp, wROSE_addr)
    wROSE_bal = wROSE.balanceOf(web3_config.owner)
    if wROSE_bal == 0:
        logger.warning("wROSE balance is 0")
    else:
        logger.info("Found %s wROSE, converting to ROSE...", wROSE_bal.to_eth().amt_eth)
        wROSE.withdraw(wROSE_bal)

    logger.info("ROSE reward claim done")
