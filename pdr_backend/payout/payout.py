import logging
import time
from typing import Any, List

from enforce_typing import enforce_types

from pdr_backend.contract.dfrewards import DFRewards
from pdr_backend.contract.pred_submitter_mgr import PredSubmitterMgr
from pdr_backend.contract.feed_contract import FeedContract
from pdr_backend.contract.wrapped_token import WrappedToken
from pdr_backend.predictoor.util import find_shared_slots, to_checksum
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.subgraph.subgraph_pending_payouts import query_pending_payouts
from pdr_backend.subgraph.subgraph_sync import wait_until_subgraph_syncs
from pdr_backend.util.constants import SAPPHIRE_MAINNET_CHAINID
from pdr_backend.util.currency_types import Eth, Wei

logger = logging.getLogger("payout")


@enforce_types
def batchify(data: List[Any], batch_size: int):
    return [data[i : i + batch_size] for i in range(0, len(data), batch_size)]


@enforce_types
def request_payout_batches(
    feed_contract: FeedContract, batch_size: int, timestamps: List[int]
):
    batches = batchify(timestamps, batch_size)
    for batch in batches:
        retries = 0
        success = False

        print(".", end="", flush=True)

        while retries < 5 and not success:
            try:
                wait_for_receipt = True
                feed_contract.payout_multiple(batch, wait_for_receipt)
                success = True
            except Exception as e:
                retries += 1
                logger.warning("Error: %s. Retrying... %d/5", e, retries)
                time.sleep(1)

        if not success:
            logger.error("Failed after 5 attempts. Moving to next batch.")

    logger.info("Batch completed")


@enforce_types
def find_slots_and_payout_with_mgr(pred_submitter_mgr, ppss):
    # we only need to query in one direction, since both predict on the same slots
    up_addr = pred_submitter_mgr.pred_submitter_up_address()
    web3_config = ppss.web3_pp.web3_config
    subgraph_url: str = ppss.web3_pp.subgraph_url
    logger.info("Starting payout")
    wait_until_subgraph_syncs(web3_config, subgraph_url)
    logger.info("Finding pending payouts")
    pending_slots = query_pending_payouts(subgraph_url, up_addr)
    shared_slots = find_shared_slots(pending_slots)
    if not shared_slots:
        logger.info("No payouts available")
        return
    logger.info("Found %d slots", len(shared_slots))
    for slot_tuple in shared_slots:
        contract_addrs, slots = slot_tuple
        contract_addrs = to_checksum(ppss.web3_pp.w3, contract_addrs)
        tx = pred_submitter_mgr.get_payout(slots, contract_addrs)
        cur_index = shared_slots.index(slot_tuple)
        progress = f"{cur_index + 1}/{len(shared_slots)}"
        logger.info("Payout tx %s: %s", progress, tx["transactionHash"].hex())
    logger.info("Payout done")


@enforce_types
def do_ocean_payout(ppss: PPSS, check_network: bool = True):
    web3_config = ppss.web3_pp.web3_config
    if check_network:
        assert ppss.web3_pp.network == "sapphire-mainnet"
        assert web3_config.w3.eth.chain_id == SAPPHIRE_MAINNET_CHAINID

    pred_submitter_mgr_addr = ppss.predictoor_ss.pred_submitter_mgr
    pred_submitter_mgr = PredSubmitterMgr(ppss.web3_pp, pred_submitter_mgr_addr)

    find_slots_and_payout_with_mgr(pred_submitter_mgr, ppss)


@enforce_types
def do_rose_payout(ppss: PPSS, check_network: bool = True):
    web3_config = ppss.web3_pp.web3_config

    if check_network:
        assert ppss.web3_pp.network == "sapphire-mainnet"
        assert web3_config.w3.eth.chain_id == SAPPHIRE_MAINNET_CHAINID

    web3_config = ppss.web3_pp.web3_config
    pred_submitter_mgr_addr = ppss.predictoor_ss.pred_submitter_mgr
    pred_submitter_mgr = PredSubmitterMgr(ppss.web3_pp, pred_submitter_mgr_addr)
    up_addr = pred_submitter_mgr.pred_submitter_up_address()
    down_addr = pred_submitter_mgr.pred_submitter_down_address()

    dfrewards_addr = "0xc37F8341Ac6e4a94538302bCd4d49Cf0852D30C0"
    wROSE_addr = "0x8Bc2B030b299964eEfb5e1e0b36991352E56D2D3"
    wROSE = WrappedToken(ppss.web3_pp, wROSE_addr)

    dfrewards_contract = DFRewards(ppss.web3_pp, dfrewards_addr)
    claimable_rewards_up = dfrewards_contract.get_claimable_rewards(up_addr, wROSE_addr)
    claimable_rewards_down = dfrewards_contract.get_claimable_rewards(
        down_addr, wROSE_addr
    )
    total_claimable = claimable_rewards_up + claimable_rewards_down
    logger.info("Found %s wROSE available to claim", total_claimable.to_eth().amt_eth)

    if total_claimable > Eth(0):
        logger.info("Claiming wROSE rewards from the manager contract...")
        receipt = pred_submitter_mgr.claim_dfrewards(wROSE_addr, dfrewards_addr, True)
        if receipt["status"] != 1:
            logger.warning(
                "Failed to claim wROSE rewards from the contract, tx: %s",
                receipt["transactionHash"],
            )
            return
        logger.info("Transfering wROSE to owner")
        time.sleep(4)
        balance = wROSE.balanceOf(pred_submitter_mgr.contract_address)
        receipt = pred_submitter_mgr.transfer_erc20(
            wROSE_addr, web3_config.owner, balance, True
        )
        if receipt["status"] != 1:
            logger.warning(
                "Failed to transfer wROSE tokens to the owner, tx: %s",
                receipt["transactionHash"],
            )
            return
    else:
        logger.warning("No rewards available to claim")
        return

    logger.info("Converting wROSE to ROSE")
    time.sleep(4)
    wROSE_bal = wROSE.balanceOf(web3_config.owner)
    if wROSE_bal == Wei(0):
        logger.warning("wROSE balance is 0")
    else:
        logger.info("Found %s wROSE, converting to ROSE...", wROSE_bal.to_eth().amt_eth)
        wROSE.withdraw(wROSE_bal)

    logger.info("ROSE reward claim done")
