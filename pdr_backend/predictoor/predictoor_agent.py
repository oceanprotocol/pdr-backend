import logging
import os
import time
from collections import defaultdict
from typing import Dict, List, Tuple

from enforce_typing import enforce_types

from pdr_backend.aimodel.aimodel_data_factory import AimodelDataFactory
from pdr_backend.aimodel.aimodel_factory import AimodelFactory
from pdr_backend.cli.predict_train_feedsets import PredictTrainFeedset
from pdr_backend.contract.pred_submitter_mgr import PredSubmitterMgr
from pdr_backend.contract.token import NativeToken, Token
from pdr_backend.lake.ohlcv_data_factory import OhlcvDataFactory
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.predictoor.stakes_per_slot import StakeTup, StakesPerSlot
from pdr_backend.predictoor.util import find_shared_slots
from pdr_backend.subgraph.subgraph_feed import print_feeds, SubgraphFeed
from pdr_backend.subgraph.subgraph_pending_payouts import query_pending_payouts
from pdr_backend.util.currency_types import Eth, Wei
from pdr_backend.util.logutil import logging_has_stdout
from pdr_backend.util.time_types import UnixTimeS

logger = logging.getLogger("predictoor_agent")
MAX_WEI = Wei(2**256 - 1)


# pylint: disable=too-many-public-methods
class PredictoorAgent:
    """
    What it does
    - Fetches Predictoor contracts from subgraph, and filters them
    - Monitors each contract for epoch changes.
    - When a value can be predicted, call calc_stakes()

    Prediction is two-sided: it submits for both up and down directions,
      with a stake for each.
    """

    # pylint: disable=too-many-instance-attributes
    @enforce_types
    def __init__(self, ppss: PPSS):
        # ppss
        self.ppss = ppss
        logger.info(self.ppss)

        pred_submitter_mgr_addr = self.ppss.predictoor_ss.pred_submitter_mgr
        if not pred_submitter_mgr_addr:
            raise ValueError("No pred_submitter_mgr_addr is set.")
        self.pred_submitter_mgr = PredSubmitterMgr(
            self.ppss.web3_pp, pred_submitter_mgr_addr
        )

        cand_feeds: Dict[str, SubgraphFeed] = ppss.web3_pp.query_feed_contracts()
        print_feeds(cand_feeds, f"cand feeds, owner={ppss.web3_pp.owner_addrs}")

        self.feeds: Dict[str, SubgraphFeed] = (
            ppss.predictoor_ss.get_feed_from_candidates(cand_feeds)
        )

        if len(self.feeds) == 0:
            raise ValueError("No feeds found.")

        print_feeds(self.feeds, "filtered feed")

        feed_addrs: List[str] = list(self.feeds.keys())
        feed_addrs = self._to_checksum(feed_addrs)

        logger.info("Approving tokens...")
        self.OCEAN.approve(self.pred_submitter_mgr.contract_address, MAX_WEI)
        self.pred_submitter_mgr.approve_ocean(feed_addrs)
        logger.info("Tokens approved")

        # ensure ohlcv data cache is up to date
        if self.use_ohlcv_data():
            _ = self.get_ohlcv_data()

        # set attribs to track block
        self.prev_block_timestamp: UnixTimeS = UnixTimeS(0)
        self.prev_block_number: UnixTimeS = UnixTimeS(0)
        self.prev_submit_epochs: List[int] = []
        self.prev_submit_payouts: List[int] = []

    @enforce_types
    def run(self):
        logger.info("Starting main loop.")
        logger.info("Waiting...")
        while True:
            self.take_step()
            if os.getenv("TEST") == "true":
                break

    @enforce_types
    def calc_stakes_across_feeds(self, feeds: List[SubgraphFeed]) -> StakesPerSlot:
        stakes = StakesPerSlot()
        prediction_objs = []
        epoch_cache: Dict[str, int] = defaultdict(int)

        # First pass: Collect data and prepare predictions
        for feed in feeds:
            contract = self.ppss.web3_pp.get_single_contract(feed.address)
            feedset = self.ppss.predictoor_ss.get_predict_train_feedset(
                feed.source, feed.pair, feed.timeframe
            )

            if feedset is None:
                logger.error("No (predict, train) pair found for feed %s", feed)
                continue  # Skip further processing for this feed

            seconds_per_epoch = feed.seconds_per_epoch
            stake_up, stake_down = self.calc_stakes(feedset)

            timeframe_key = feed.timeframe
            current_epoch = epoch_cache.setdefault(
                timeframe_key, contract.get_current_epoch()
            )

            target_slot = UnixTimeS((current_epoch + 2) * seconds_per_epoch)
            prediction_objs.append(
                (feed, stake_up, stake_down, target_slot, seconds_per_epoch, contract)
            )

        epoch_cache.clear()  # Reset cache

        # Second pass: Add stakes based on predictions and current time conditions
        for (
            feed,
            stake_up,
            stake_down,
            target_slot,
            seconds_per_epoch,
            contract,
        ) in prediction_objs:
            timeframe_key = feed.timeframe
            current_epoch = epoch_cache.setdefault(
                timeframe_key, contract.get_current_epoch()
            )

            next_slot = (current_epoch + 1) * seconds_per_epoch
            expected_target_slot = next_slot + seconds_per_epoch
            cur_epoch_s_left = next_slot - self.cur_timestamp

            if (
                cur_epoch_s_left > self.epoch_s_thr
                or target_slot != expected_target_slot
            ):
                continue  # Skip if the time left is greater than threshold or in a different epoch
            up_stake_percentage = (
                stake_up.amt_eth / (stake_up.amt_eth + stake_down.amt_eth) * 100
            )
            feed_str = f"{feed.source} {feed.pair} {feed.timeframe} {feed.address[:6]}"
            log_msg = f"Predicted feed {feed_str}, "
            log_msg += f"slot: {target_slot}: up = {stake_up.amt_eth:.2f} OCEAN"
            log_msg += f" down = {stake_down.amt_eth:.2f} OCEAN ({up_stake_percentage:.2f}% up)"
            logger.info(log_msg)
            stakes.add_stake_at_slot(target_slot, StakeTup(feed, stake_up, stake_down))

        return stakes

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

        # get payouts
        self.get_payout()

        # --- Prediction ---
        if self.min_epoch_s_left > self.epoch_s_thr:
            # not time to predict yet
            return
        # for each feed, calculate up/down stake (eg via models)
        feeds = list(self.feeds.values())
        logger.info("Calculating predictions and stakes")
        stakes: StakesPerSlot = self.calc_stakes_across_feeds(feeds)

        if len(stakes.slots) == 0:
            logger.info("No predictions to submit, skipping")

        # submit prediction txs
        for target_slot in stakes.target_slots:
            stakes_up, stakes_down, feed_addrs = stakes.get_stake_lists(target_slot)
            feed_addrs = self._to_checksum(feed_addrs)

            required_OCEAN = Eth(0)
            for stake in stakes_up + stakes_down:
                required_OCEAN += stake
            if not self.check_balances(required_OCEAN):
                logger.error(
                    "Address %s does not have enough OCEAN balance, cancel prediction",
                    self.ppss.web3_pp.web3_config.owner,
                )
                return

            logger.info(self.status_str())
            s = f"-> Predict result: {stakes_up} up, {stakes_down} down"
            s += f", feeds={feed_addrs}, time slot={target_slot}"
            logger.debug(s)

            if required_OCEAN == Eth(0):
                logger.warning("Done: no predictions to submit")
                return

            # submit prediction to chain
            self.submit_prediction_txs(
                stakes_up,
                stakes_down,
                target_slot,
                feed_addrs,
            )
            self.prev_submit_epochs.append(target_slot)

            # start printing for next round
            if logging_has_stdout():
                print("" + "=" * 180)
            logger.info(self.status_str())
            logger.info("Waiting...")

    @enforce_types
    def _to_checksum(self, addrs: List[str]) -> List[str]:
        w3 = self.ppss.web3_pp.w3
        checksummed_addrs = [w3.to_checksum_address(addr) for addr in addrs]
        return checksummed_addrs

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
    def min_epoch_s_left(self):
        """
        Returns the closest epoch time left in seconds
        """
        min_tf_seconds = (
            self.ppss.predictoor_ss.predict_train_feedsets.min_epoch_seconds
        )
        current_ts = self.cur_timestamp
        seconds_left = min_tf_seconds - current_ts % min_tf_seconds
        return seconds_left

    @property
    def cur_unique_epoch(self):
        """
        Returns the unique epoch number for the current timestamp
        """
        t = self.cur_timestamp
        min_tf_seconds = (
            self.ppss.predictoor_ss.predict_train_feedsets.min_epoch_seconds
        )
        return t // min_tf_seconds

    @property
    def s_start_payouts(self) -> int:
        """Run payout when there's this seconds left"""
        return self.ppss.predictoor_ss.s_start_payouts

    @property
    def epoch_s_thr(self):
        """Start predicting if there's > this time left"""
        return self.ppss.predictoor_ss.s_until_epoch_end

    @property
    def OCEAN(self) -> Token:
        return self.ppss.web3_pp.OCEAN_Token

    @property
    def ROSE(self) -> NativeToken:
        return self.ppss.web3_pp.NativeToken

    def status_str(self) -> str:
        s = ""
        s += f"cur_epoch={self.cur_unique_epoch}"
        s += f", cur_block_number={self.cur_block_number}"
        s += f", cur_timestamp={self.cur_timestamp}"
        s += f". {self.min_epoch_s_left} s left in closest epoch"
        s += f" (predict if <= {self.epoch_s_thr} s left)"
        return s

    @enforce_types
    def submit_prediction_txs(
        self,
        stakes_up: List[Eth],
        stakes_down: List[Eth],
        target_slot: UnixTimeS,  # a timestamp
        feed_addrs: List[str],
    ):
        logger.info("Submitting predictions to the chain...")
        stakes_up_wei = [i.to_wei() for i in stakes_up]
        stakes_down_wei = [i.to_wei() for i in stakes_down]
        tx = self.pred_submitter_mgr.submit_prediction(
            stakes_up=stakes_up_wei,
            stakes_down=stakes_down_wei,
            feed_addrs=feed_addrs,
            epoch=target_slot,
        )
        logger.info("Tx submitted %s", tx["transactionHash"].hex())

        # handle errors
        if _tx_failed(tx):
            s = "Tx failed"
            s += f"\ntx1={tx.transactionHash.hex()}"
            logger.warning(s)

    @enforce_types
    def calc_stakes(self, feedset: PredictTrainFeedset) -> Tuple[Eth, Eth]:
        """
        @return
          stake_up -- amt to stake up, in units of Eth
          stake_down -- amt to stake down, ""
        """
        approach = self.ppss.predictoor_ss.approach
        if approach == 1:
            return self.calc_stakes1()
        if approach == 2:
            return self.calc_stakes2(feedset)
        if approach == 3:
            return self.calc_stakes3(feedset)
        raise ValueError("Approach not supported")

    @enforce_types
    def calc_stakes1(self) -> Tuple[Eth, Eth]:
        """
        @description
          Calculate up-vs-down stake according to approach 1.
          How: allocate equally (50-50)

        @return
          stake_up -- amt to stake up, in units of Eth
          stake_down -- amt to stake down, ""
        """
        assert self.ppss.predictoor_ss.approach == 1
        tot_amt = self.ppss.predictoor_ss.stake_amount
        stake_up, stake_down = tot_amt * 0.50 * tot_amt, tot_amt * 0.50
        return (stake_up, stake_down)

    @enforce_types
    def calc_stakes2(self, feedset: PredictTrainFeedset) -> Tuple[Eth, Eth]:
        """
        @description
          Calculate up-vs-down stake according to approach 2.
          How: use classifier model's confidence, two-sided

        @return
          stake_up -- amt to stake up, in units of Eth
          stake_down -- amt to stake down, ""
        """
        assert self.ppss.predictoor_ss.approach == 2
        (stake_up, stake_down) = self.calc_stakes_2ss_model(feedset)
        return (stake_up, stake_down)

    @enforce_types
    def calc_stakes3(self, feedset) -> Tuple[Eth, Eth]:
        """
        @description
          Calculate up-vs-down stake according to approach 3.
          How: Like approach 2, but one-sided difference of (larger - smaller)

        @return
          stake_up -- amt to stake up, in units of Eth
          stake_down -- amt to stake down, ""
        """
        assert self.ppss.predictoor_ss.approach == 3
        (stake_up, stake_down) = self.calc_stakes_2ss_model(feedset)
        if stake_up == stake_down:
            return (Eth(0), Eth(0))

        if stake_up > stake_down:
            return (stake_up - stake_down, Eth(0))

        # stake_up < stake_down
        return (Eth(0), stake_down - stake_up)

    @enforce_types
    def calc_stakes_2ss_model(self, feedset) -> Tuple[Eth, Eth]:
        """
        @description
          Model-based calculate up-vs-down stake.
          How: use classifier model's confidence

        @return
          stake_up -- amt to stake up, in units of Eth
          stake_down -- amt to stake down, ""
        """
        mergedohlcv_df = self.get_ohlcv_data()

        data_f = AimodelDataFactory(self.ppss.predictoor_ss)
        X, ycont, _, xrecent = data_f.create_xy(
            mergedohlcv_df,
            testshift=0,
            predict_feed=feedset.predict,
            train_feeds=feedset.train_on,
        )

        curprice = ycont[-1]
        y_thr = curprice
        ybool = data_f.ycont_to_ytrue(ycont, y_thr)

        # build model
        model_f = AimodelFactory(self.ppss.predictoor_ss.aimodel_ss)
        model = model_f.build(X, ybool)

        # predict
        X_test = xrecent.reshape((1, len(xrecent)))
        prob_up = model.predict_ptrue(X_test)[0]

        # calc stake amounts
        tot_amt = self.ppss.predictoor_ss.stake_amount
        stake_up = tot_amt * prob_up
        stake_down = tot_amt * (1.0 - prob_up)

        return (stake_up, stake_down)

    @enforce_types
    def use_ohlcv_data(self) -> bool:
        """Do we use ohlcv data?"""
        return self.ppss.predictoor_ss.approach in [2, 3]

    @enforce_types
    def get_ohlcv_data(self):
        """Update local lake's ohlcv data; return the data frame that results"""
        if not self.use_ohlcv_data():
            raise ValueError("only call if we need ohlcv data")
        f = OhlcvDataFactory(self.ppss.lake_ss)
        mergedohlcv_df = f.get_mergedohlcv_df()
        return mergedohlcv_df

    @enforce_types
    def check_balances(self, required_OCEAN: Eth) -> bool:
        min_ROSE_bal = Eth(1).to_wei()

        # check OCEAN balance
        OCEAN_bal = self.OCEAN.balanceOf(self.ppss.web3_pp.web3_config.owner)
        if OCEAN_bal < required_OCEAN.to_wei():
            logger.error("OCEAN balance too low: %s < %s", OCEAN_bal, required_OCEAN)
            return False

        # check ROSE balance
        ROSE_bal = self.ROSE.balanceOf(self.ppss.web3_pp.web3_config.owner)
        if ROSE_bal < min_ROSE_bal:
            logger.error("ROSE balance too low: %s < %s", ROSE_bal, min_ROSE_bal)
            return False

        return True

    @enforce_types
    def get_payout(self):
        """Claims payouts"""
        if (
            self.s_start_payouts == 0
            or self.min_epoch_s_left >= self.s_start_payouts
            or self.cur_unique_epoch in self.prev_submit_payouts
        ):
            return

        logger.info(self.status_str())
        logger.info("Running payouts")

        # Update previous payouts history to avoid claiming for this epoch again
        self.prev_submit_payouts.append(self.cur_unique_epoch)

        up_pred_addr = self.pred_submitter_mgr.predictoor_up_address()
        pending_slots = query_pending_payouts(
            self.ppss.web3_pp.subgraph_url, up_pred_addr
        )
        shared_slots = find_shared_slots(pending_slots)
        if not shared_slots:
            logger.info("No payouts available")
            return

        for slot_tuple in shared_slots:
            contract_addrs, slots = slot_tuple
            contract_addrs = self._to_checksum(contract_addrs)  
            tx = self.pred_submitter_mgr.get_payout(slots, contract_addrs)

            cur_index = shared_slots.index(slot_tuple)
            progress = f"{cur_index + 1}/{len(shared_slots)}"
            logger.info("Payout tx %s: %s", progress, tx["transactionHash"].hex())


@enforce_types
def _tx_failed(tx) -> bool:
    return tx is None or tx["status"] != 1
