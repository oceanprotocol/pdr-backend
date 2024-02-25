from abc import ABC, abstractmethod
import copy
import logging
import os
import time
from typing import List, Tuple

from enforce_typing import enforce_types

from pdr_backend.ppss.ppss import PPSS
from pdr_backend.subgraph.subgraph_feed import print_feeds
from pdr_backend.util.logutil import logging_has_stdout
from pdr_backend.util.mathutil import sole_value
from pdr_backend.util.time_types import UnixTimeS
from pdr_backend.util.web3_config import Web3Config

logger = logging.getLogger("predictoor_agent")


class BasePredictoorAgent(ABC):
    """
    What it does
    - Fetches Predictoor contracts from subgraph, and filters them
    - Monitors each contract for epoch changes.
    - When a value can be predicted, call get_prediction()
    """

    @enforce_types
    def __init__(self, ppss: PPSS):
        # ppss
        self.ppss = ppss
        logger.info(self.ppss)

        # set self.feeds
        cand_feeds = ppss.web3_pp.query_feed_contracts()
        print_feeds(cand_feeds, f"cand feeds, owner={ppss.web3_pp.owner_addrs}")

        feed = ppss.predictoor_ss.get_feed_from_candidates(cand_feeds)
        if not feed:
            raise ValueError("No feeds found.")

        print_feeds({feed.address: feed}, "filtered feed")
        self.feed = feed

        contracts = ppss.web3_pp.get_contracts([feed.address])
        self.feed_contract = sole_value(contracts)

        pk2 = os.getenv("PRIVATE_KEY2")
        assert pk2 is not None, "Need PRIVATE_KEY2 envvar"
        rpc_url = self.feed_contract.web3_pp.rpc_url
        web3_config2 = Web3Config(rpc_url, pk2)
        self.feed_contract2 = copy.deepcopy(self.feed_contract)
        self.feed_contract2.web3_pp.set_web3_config(web3_config2)

        # set attribs to track block
        self.prev_block_timestamp: UnixTimeS = UnixTimeS(0)
        self.prev_block_number: UnixTimeS = UnixTimeS(0)
        self.prev_submit_epochs: List[int] = []

    @enforce_types
    def run(self):
        logger.info("Starting main loop.")
        logger.info(self.status_str())
        logger.info("Waiting...")
        while True:
            self.take_step()
            if os.getenv("TEST") == "true":
                break

    @enforce_types
    def take_step(self):
        # at new block number yet?
        if self.cur_block_number <= self.prev_block_number:
            if logging_has_stdout():
                print(".", end="", flush=True)
            time.sleep(1)
            return

        # is new block ready yet?
        if not self.cur_block:
            return
        self.prev_block_number = UnixTimeS(self.cur_block_number)
        self.prev_block_timestamp = UnixTimeS(self.cur_timestamp)

        # within the time window to predict?
        if self.cur_epoch_s_left > self.epoch_s_thr:
            return

        logger.info(self.status_str())

        # compute prediction; exit if no good
        submit_epoch, target_slot = self.cur_epoch, self.target_slot
        logger.info("Predict for time slot = %s...", self.target_slot)

        stake_up, stake_down = self.get_prediction(target_slot)
        s = f"-> Predict result: stake_up={stake_up}, stake_down={stake_down}"
        logger.info(s)
        if stake_up == 0 and stake_down == 0:
            logger.warning("Done: can't use predval/stake")
            return

        # submit prediction to chain
        self.submit_prediction_txs(stake_up, stake_down, target_slot)
        self.prev_submit_epochs.append(submit_epoch)

        # start printing for next round
        if logging_has_stdout():
            print("" + "=" * 180)
        logger.info(self.status_str())
        logger.info("Waiting...")

        
    @enforce_types
    def submit_prediction_txs(
            self,
            stake_up: float, # in units of Eth
            stake_down: float, # ""
            target_slot : int, # a timestamp
    ):
        logger.info("Submit 'up' prediction tx to chain...")
        tx1 = self.feed_contract.submit_prediction(
            True,
            stake_up,
            target_slot,
            wait_for_receipt=True,
        )
        
        logger.info("Submit 'down' prediction tx to chain...")
        tx2 = self.feed_contract2.submit_prediction(
            False,
            stake_down,
            target_slot,
            wait_for_receipt=True,
        )

        # handle errors
        if _tx_failed(tx1) or _tx_failed(tx2):
            s = "One or both txs failed. So, resubmit both with zero stake."
            s += f"\ntx1={tx1}\ntx2={tx2}"
            logger.warning(s)

            logger.info("Re-submit 'up' prediction tx to chain... (stake=0)")
            self.feed_contract.submit_prediction(
                True,
                1e-10,
                target_slot,
                wait_for_receipt=True,
            )
            
            logger.info("Re-submit 'down' prediction tx to chain... (stake=0)")
            self.feed_contract2.submit_prediction(
                False,
                1e-10,
                target_slot,
                wait_for_receipt=True,
            )

        return True

    @property
    def cur_epoch(self) -> int:
        return self.feed_contract.get_current_epoch()

    @property
    def cur_block(self):
        return self.ppss.web3_pp.web3_config.get_block(
            self.cur_block_number, full_transactions=False
        )

    @property
    def cur_block_number(self) -> int:
        return self.ppss.web3_pp.w3.eth.block_number

    @property
    def cur_timestamp(self) -> UnixTimeS:
        return UnixTimeS(self.cur_block["timestamp"])

    @property
    def epoch_s_thr(self):
        """Start predicting if there's > this time left"""
        return self.ppss.predictoor_ss.s_until_epoch_end

    @property
    def s_per_epoch(self) -> int:
        return self.feed.seconds_per_epoch

    @property
    def next_slot(self) -> UnixTimeS:  # a timestamp
        return UnixTimeS((self.cur_epoch + 1) * self.s_per_epoch)

    @property
    def target_slot(self) -> int:  # a timestamp
        return UnixTimeS((self.cur_epoch + 2) * self.s_per_epoch)

    @property
    def cur_epoch_s_left(self) -> int:
        return self.next_slot - self.cur_timestamp

    def status_str(self) -> str:
        s = ""
        s += f"cur_epoch={self.cur_epoch}"
        s += f", cur_block_number={self.cur_block_number}"
        s += f", cur_timestamp={self.cur_timestamp}"
        s += f", next_slot={self.next_slot}"
        s += f", target_slot={self.target_slot}"
        s += f". {self.cur_epoch_s_left} s left in epoch"
        s += f" (predict if <= {self.epoch_s_thr} s left)"
        s += f". s_per_epoch={self.s_per_epoch}"
        return s

    @abstractmethod
    def get_prediction(
        self,
        timestamp: UnixTimeS,  # pylint: disable=unused-argument
    ) -> Tuple[bool, float]:
        pass

@enforce_types
def _tx_failed(tx) -> bool:
    return tx is None or tx["status"] != 1
