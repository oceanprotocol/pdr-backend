import logging
import os
import time
from typing import Dict, List, Tuple

from enforce_typing import enforce_types

from pdr_backend.aimodel.aimodel_data_factory import AimodelDataFactory
from pdr_backend.aimodel.aimodel_factory import AimodelFactory
from pdr_backend.contract.pred_submitter_mgr import PredSubmitterMgr
from pdr_backend.contract.feed_contract import FeedContract
from pdr_backend.contract.token import NativeToken, Token
from pdr_backend.lake.ohlcv_data_factory import OhlcvDataFactory
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.subgraph.subgraph_feed import print_feeds, SubgraphFeed
from pdr_backend.util.logutil import logging_has_stdout
from pdr_backend.util.time_types import UnixTimeS
from pdr_backend.util.currency_types import Eth

logger = logging.getLogger("predictoor_agent")


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
        logger.info(self.status_str())
        logger.info("Waiting...")
        while True:
            self.take_step()
            if os.getenv("TEST") == "true":
                break

    @enforce_types
    def prepare_stakes(self, feeds: List[SubgraphFeed]):
        stakes_up = []
        stakes_down = []
        feed_addrs = []

        seconds_per_epoch = None
        cur_epoch = None

        for feed in feeds:
            contract = self.ppss.web3_pp.get_single_contract(feed.address)
            if seconds_per_epoch is None:
                # this is same for all feeds
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
            stake_up, stake_down = self.calc_stakes(feed)

            # add to lists
            stakes_up.append(stake_up)
            stakes_down.append(stake_down)
            feed_addrs.append(feed.address)

        target_slot = UnixTimeS((cur_epoch + 2) * seconds_per_epoch)

        return stakes_up, stakes_down, feed_addrs, target_slot

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


        stakes_up, stakes_down, feed_addrs, target_slot = self.prepare_stakes(self.feeds)
        required_OCEAN = sum(stakes_up) + sum(stakes_down)
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
    def s_per_epoch(self) -> int:
        return self.feeds[0].seconds_per_epoch

    @property
    def next_slot(self) -> UnixTimeS:  # a timestamp
        return UnixTimeS((self.cur_epoch + 1) * self.s_per_epoch)

    @property
    def target_slot(self) -> UnixTimeS:  # a timestamp
        return UnixTimeS((self.cur_epoch + 2) * self.s_per_epoch)

    @property
    def cur_epoch_s_left(self) -> int:
        return self.next_slot - self.cur_timestamp

    @property
    def OCEAN(self) -> Token:
        return self.ppss.web3_pp.OCEAN_Token

    @property
    def ROSE(self) -> NativeToken:
        return self.ppss.web3_pp.NativeToken

    def status_str(self) -> str:
        s = ""
        s += f"cur_epoch={self.cur_epoch}"
        s += f", cur_block_number={self.cur_block_number}"
        s += f", cur_timestamp={self.cur_timestamp}"
        s += f", next_slot={self.next_slot}"
        s += f", target_slot={self.target_slot}"
        s += f". {self.cur_epoch_s_left} s left in epoch"
        s += f" (predict if <= {self.epoch_s_thr} s left)"
        s += f" (stop predictions if <= {self.s_cutoff} s left)"
        s += f". s_per_epoch={self.s_per_epoch}"
        return s

    @enforce_types
    def submit_prediction_txs(
        self,
        stakes_up: List[Eth],
        stakes_down: List[Eth],
        feeds: List[str],
        target_slot: UnixTimeS,  # a timestamp
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
            s = "Tx failed So, resubmit both with zero stake."
            s += f"\ntx1={tx}"
            logger.warning(s)

    @enforce_types
    def calc_stakes(self, feed: SubgraphFeed) -> Tuple[Eth, Eth]:
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
    def calc_stakes2(self) -> Tuple[Eth, Eth]:
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
        X, ycont, _, xrecent = data_f.create_xy(mergedohlcv_df, testshift=0)

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
    def check_balances(self, required_OCEAN: int) -> bool:
        min_ROSE_bal = Eth(1).to_wei()

        # check OCEAN balance
        OCEAN_bal = self.OCEAN.balanceOf(self.pred_submitter_mgr.contract_address)
        if OCEAN_bal < required_OCEAN:
            logger.error("OCEAN balance too low: %s < %s", OCEAN_bal, required_OCEAN)
            return False

        # check ROSE balance
        ROSE_bal = self.ROSE.get_balance()
        if ROSE_bal < min_ROSE_bal:
            logger.error("ROSE balance too low: %s < %s", ROSE_bal, min_ROSE_bal)
            return False

        return True

    def get_payout(self):
        """Claims payouts"""
        if (
            self.s_start_payouts == 0
            or self.cur_epoch_s_left >= self.s_start_payouts
            or self.cur_epoch in self.prev_submit_payouts
        ):
            return

        logger.info("Running payouts")

        # TODO Implement manager payout here.

        # Update previous payouts history to avoid claiming for this epoch again
        self.prev_submit_payouts.append(self.cur_epoch)


@enforce_types
def _tx_failed(tx) -> bool:
    return tx is None or tx["status"] != 1
