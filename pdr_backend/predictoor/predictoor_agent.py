import logging
import os
import time
from typing import Dict, List, Tuple

from enforce_typing import enforce_types

from pdr_backend.aimodel.aimodel_data_factory import AimodelDataFactory
from pdr_backend.aimodel.aimodel_factory import AimodelFactory
from pdr_backend.cli.predict_feeds import PredictFeed
from pdr_backend.contract.pred_submitter_mgr import PredSubmitterMgr
from pdr_backend.contract.token import NativeToken, Token
from pdr_backend.lake.ohlcv_data_factory import OhlcvDataFactory
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.subgraph.subgraph_feed import print_feeds, SubgraphFeed
from pdr_backend.subgraph.subgraph_pending_payouts import query_pending_payouts
from pdr_backend.util.logutil import logging_has_stdout
from pdr_backend.util.time_types import UnixTimeS
from pdr_backend.util.currency_types import Eth

logger = logging.getLogger("predictoor_agent")


class PredictionSlotsData:
    def __init__(self):
        self.target_slots = {}

    def add_prediction(self, slot, feed, stake_up, stake_down):
        if slot not in self.target_slots:
            self.target_slots[slot] = []
        self.target_slots[slot].append((feed, stake_up, stake_down))

    def get_predictions(self, slot):
        return self.target_slots.get(slot, [])

    def get_predictions_arr(self, slot):
        stakes_up = []
        stakes_down = []
        feed_addrs = []

        for feed, stake_up, stake_down in self.get_predictions(slot):
            stakes_up.append(stake_up)
            stakes_down.append(stake_down)
            feed_addrs.append(feed.address)

        return stakes_up, stakes_down, feed_addrs

    @property
    def slots(self):
        return list(self.target_slots.keys())


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

        # set self.feed
        cand_feeds: Dict[str, SubgraphFeed] = ppss.web3_pp.query_feed_contracts()
        checksummed_addresses = [
            self.ppss.web3_pp.web3_config.w3.to_checksum_address(addr)
            for addr in cand_feeds.keys()
        ]
        self.pred_submitter_mgr.approve_ocean(checksummed_addresses)
        print_feeds(cand_feeds, f"cand feeds, owner={ppss.web3_pp.owner_addrs}")

        feeds: SubgraphFeed = ppss.predictoor_ss.filter_feeds_from_candidates(
            cand_feeds
        )
        if len(feeds) == 0:
            raise ValueError("No feeds found.")

        print_feeds(feeds, "filtered feed")
        self.feeds: SubgraphFeed = feeds

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
    def prepare_stakes(self, feeds: List[SubgraphFeed]) -> PredictionSlotsData:
        slot_data = PredictionSlotsData()

        seconds_per_epoch = None
        cur_epoch = None

        for feed in feeds:
            contract = self.ppss.web3_pp.get_single_contract(feed.address)
            predict_pair = self.ppss.predictoor_ss.get_predict_feed(
                feed.pair, feed.timeframe, feed.source
            )
            seconds_per_epoch = feed.seconds_per_epoch
            cur_epoch = contract.get_current_epoch()
            next_slot = UnixTimeS((cur_epoch + 1) * seconds_per_epoch)
            cur_epoch_s_left = next_slot - self.cur_timestamp

            # within the time window to predict?
            if cur_epoch_s_left > self.epoch_s_thr:
                continue
            if cur_epoch_s_left < self.s_cutoff:
                break

            # get the target slot

            # get the stakes
            stake_up, stake_down = self.calc_stakes(predict_pair)
            target_slot = UnixTimeS((cur_epoch + 2) * seconds_per_epoch)
            slot_data.add_prediction(target_slot, feed, stake_up, stake_down)

        return slot_data

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
        # set predictoor_ss.bot_only.s_start_payouts to 0 to disable auto payouts
        self.get_payout()

        logger.info(self.status_str())

        slot_data = self.prepare_stakes(list(self.feeds.values()))

        for target_slot in slot_data.slots:
            stakes_up, stakes_down, feed_addrs = slot_data.get_predictions_arr(
                target_slot
            )
            feed_addrs = [
                self.ppss.web3_pp.web3_config.w3.to_checksum_address(addr)
                for addr in feed_addrs
            ]

            required_OCEAN = Eth(0)
            for stake in stakes_up + stakes_down:
                required_OCEAN += stake
            if not self.check_balances(required_OCEAN):
                logger.error("Not enough balance, cancel prediction")
                return

            s = f"-> Predict result: {stakes_up} up, {stakes_down} down, feeds={feed_addrs}"
            logger.info(s)
            if required_OCEAN == 0:
                logger.warning("Done: no stakes to submit")
                return

            # submit prediction to chaineds]
            self.submit_prediction_txs(stakes_up, stakes_down, target_slot, feed_addrs)
            self.prev_submit_epochs.append(target_slot)

            # start printing for next round
            if logging_has_stdout():
                print("" + "=" * 180)
            logger.info(self.status_str())
            logger.info("Waiting...")

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
        min_tf_seconds = self.ppss.predictoor_ss.feeds.min_epoch_seconds
        current_ts = self.cur_timestamp

        seconds_left = current_ts % min_tf_seconds
        return seconds_left

    @property
    def cur_unique_epoch(self):
        """
        Returns the unique epoch number for the current timestamp
        """
        t = self.cur_timestamp
        min_tf_seconds = self.ppss.predictoor_ss.feeds.min_epoch_seconds
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
    def s_cutoff(self):
        """Stop predicting if there's < this time left"""
        return self.ppss.predictoor_ss.s_cutoff

    @property
    def OCEAN(self) -> Token:
        return self.ppss.web3_pp.OCEAN_Token

    @property
    def ROSE(self) -> NativeToken:
        return self.ppss.web3_pp.NativeToken

    def status_str(self) -> str:
        # TODO remove deprecated values and enable this back
        s = ""
        s += f"cur_epoch={self.cur_unique_epoch}"
        s += f", cur_block_number={self.cur_block_number}"
        s += f", cur_timestamp={self.cur_timestamp}"
        s += f". {self.min_epoch_s_left} s left in closest epoch"
        s += f" (predict if <= {self.epoch_s_thr} s left)"
        s += f" (stop predictions if <= {self.s_cutoff} s left)"
        return s

    @enforce_types
    def submit_prediction_txs(
        self,
        stakes_up: List[Eth],
        stakes_down: List[Eth],
        target_slot: UnixTimeS,  # a timestamp
        feeds: List[str],
    ):
        logger.info("Submitting predictions to the chain...")
        tx = self.pred_submitter_mgr.submit_prediction(
            stakes_up=stakes_up,
            stakes_down=stakes_down,
            feeds=feeds,
            epoch=target_slot,
        )

        # handle errors
        if _tx_failed(tx):
            s = "Tx failed"
            s += f"\ntx1={tx.transactionHash.hex()}"
            logger.warning(s)

    @enforce_types
    def calc_stakes(self, feed: PredictFeed) -> Tuple[Eth, Eth]:
        """
        @return
          stake_up -- amt to stake up, in units of Eth
          stake_down -- amt to stake down, ""
        """
        approach = self.ppss.predictoor_ss.approach
        if approach == 1:
            return self.calc_stakes1()
        if approach == 2:
            return self.calc_stakes2(feed)
        raise ValueError(approach)

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
    def calc_stakes2(self, feed: PredictFeed) -> Tuple[Eth, Eth]:
        """
        @description
          Calculate up-vs-down stake according to approach 2.
          How: use classifier model's confidence

        @return
          stake_up -- amt to stake up, in units of Eth
          stake_down -- amt to stake down, ""
        """
        assert self.ppss.predictoor_ss.approach == 2

        mergedohlcv_df = self.get_ohlcv_data()

        data_f = AimodelDataFactory(self.ppss.predictoor_ss)
        X, ycont, _, xrecent = data_f.create_xy(
            mergedohlcv_df, testshift=0, feed=feed.predict, feeds=feed.train_on
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
        return self.ppss.predictoor_ss.approach == 2

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
        OCEAN_bal = self.OCEAN.balanceOf(self.pred_submitter_mgr.contract_address)
        if OCEAN_bal < required_OCEAN.to_wei():
            logger.error("OCEAN balance too low: %s < %s", OCEAN_bal, required_OCEAN)
            return False

        # check ROSE balance
        ROSE_bal = self.ROSE.balanceOf(self.ppss.web3_pp.web3_config.owner)
        if ROSE_bal < min_ROSE_bal:
            logger.error("ROSE balance too low: %s < %s", ROSE_bal, min_ROSE_bal)
            return False

        return True

    def get_payout(self):
        """Claims payouts"""
        if (
            self.s_start_payouts == 0
            or self.min_epoch_s_left >= self.s_start_payouts
            or self.cur_unique_epoch in self.prev_submit_payouts
        ):
            return

        logger.info("Running payouts")

        up_pred_addr = self.pred_submitter_mgr.predictoor_up_address()
        pending_slots = query_pending_payouts(
            self.ppss.web3_pp.subgraph_url, up_pred_addr
        )
        contracts = list(pending_slots.keys())
        contracts_checksummed = [
            self.ppss.web3_pp.web3_config.w3.to_checksum_address(addr)
            for addr in contracts
        ]
        slots = list(pending_slots.values())
        slots_flat = [item for sublist in slots for item in sublist]
        slots_unique_flat = list(set(slots_flat))
        print(contracts_checksummed, "---", slots_unique_flat)
        tx = self.pred_submitter_mgr.get_payout(
            slots_unique_flat, contracts_checksummed
        )
        print("Payout tx:", tx["transactionHash"].hex())

        # Update previous payouts history to avoid claiming for this epoch again
        self.prev_submit_payouts.append(self.cur_unique_epoch)


@enforce_types
def _tx_failed(tx) -> bool:
    return tx is None or tx["status"] != 1
