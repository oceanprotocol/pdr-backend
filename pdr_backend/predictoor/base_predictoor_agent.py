import copy
import logging
import os
import time
from abc import ABC, abstractmethod
from typing import List, Tuple, Union

from enforce_typing import enforce_types

from pdr_backend.ppss.ppss import PPSS
from pdr_backend.subgraph.subgraph_feed import print_feeds
from pdr_backend.util.logutil import logging_has_stdout
from pdr_backend.util.mathutil import sole_value

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
        if pk2 is not None:
            self.feed_contract_down = copy.deepcopy(self.feed_contract)
            self.feed_contract_down.web3_pp.web3_config = Web3Config(self.feed_contract.web3_pp.rpc_url, pk2)

        # set attribs to track block
        self.prev_block_timestamp: int = 0
        self.prev_block_number: int = 0
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
        self.prev_block_number = self.cur_block_number
        self.prev_block_timestamp = self.cur_timestamp

        # within the time window to predict?
        if self.cur_epoch_s_left > self.epoch_s_thr:
            return

        logger.info(self.status_str())

        # compute prediction; exit if no good
        submit_epoch, target_slot = self.cur_epoch, self.target_slot
        logger.info("Predict for time slot = %s...", self.target_slot)

        stake_or_predval, stake = self.get_prediction(target_slot)
        
        if isinstance(stake_or_predval, float):
            if not self.feed_contract_down:
                raise ValueError("Must set PRIVATE_KEY2 to use double sided staking.")
            # stake on each side
            stake_up = stake_or_predval
            stake_down = stake
            
            tx1 = self.feed_contract.submit_prediction(
                True,
                stake_up,
                target_slot,
                wait_for_receipt=True,
            )
            tx2 = self.feed_contract_down.submit_prediction(
                False,
                stake_down,
                target_slot,
                wait_for_receipt=True,
            )

            if tx1 == None or tx2 == None or tx1["status"] != 1 or tx2["status"] != 1:
                logger.warning("One or both txs failed, failsafing to zero stake...", tx1, tx2)
                self.feed_contract.submit_prediction(
                    True,
                    1e-10,
                    target_slot,
                    wait_for_receipt=True,
                )
                self.feed_contract_down.submit_prediction(
                    False,
                    1e-10,
                    target_slot,
                    wait_for_receipt=True,
                )     
        elif isinstance(stake_or_predval, bool):
            # predval and stake amt
            predval = stake_or_predval
            logger.info("-> Predict result: predval=%s, stake=%s", predval, stake)
            if predval is None or stake <= 0:
                logger.warning("Done: can't use predval/stake")
                return

            # submit prediction to chain
            logger.info("Submit predict tx to chain...")
            self.feed_contract.submit_prediction(
                predval,
                stake,
                target_slot,
                wait_for_receipt=True,
            )

        self.prev_submit_epochs.append(submit_epoch)
        logger.info("-> Submit predict tx result: success.")

        if logging_has_stdout():
            print("" + "=" * 180)

        # start printing for next round
        logger.info(self.status_str())
        logger.info("Waiting...")

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
    def cur_timestamp(self) -> int:
        return self.cur_block["timestamp"]

    @property
    def epoch_s_thr(self):
        """Start predicting if there's > this time left"""
        return self.ppss.predictoor_ss.s_until_epoch_end

    @property
    def s_per_epoch(self) -> int:
        return self.feed.seconds_per_epoch

    @property
    def next_slot(self) -> int:  # a timestamp
        return (self.cur_epoch + 1) * self.s_per_epoch

    @property
    def target_slot(self) -> int:  # a timestamp
        return (self.cur_epoch + 2) * self.s_per_epoch

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
        timestamp: int,  # pylint: disable=unused-argument
    ) -> Tuple[Union[bool, float], float]:
        """
        @description
            Returns the prediction for the given timestamp.

        @return
            A tuple of (bool, float) to stake on one side
            A tuple of (float, float) to stake on each side, with the first element 
            being the stake for up and the second element being the stake for down.
        """
