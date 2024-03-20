import logging
import os
import time
from typing import Dict, List, Tuple

from enforce_typing import enforce_types

from pdr_backend.aimodel.aimodel_data_factory import AimodelDataFactory
from pdr_backend.aimodel.aimodel_factory import AimodelFactory
from pdr_backend.contract.pred_submitter_mgr import PredSubmitterMgr
from pdr_backend.contract.predictoor_contract import PredictoorContract
from pdr_backend.contract.token import NativeToken, Token
from pdr_backend.lake.ohlcv_data_factory import OhlcvDataFactory
from pdr_backend.payout.payout import do_ocean_payout
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.subgraph.subgraph_feed import print_feeds, SubgraphFeed
from pdr_backend.util.logutil import logging_has_stdout
from pdr_backend.util.time_types import UnixTimeS
from pdr_backend.util.web3_config import Web3Config
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
        self.pred_submitter_mgr = PredSubmitterMgr(self.ppss.web3_pp, pred_submitter_mgr_addr)


        # set self.feed
        cand_feeds: Dict[str, SubgraphFeed] = ppss.web3_pp.query_feed_contracts()
        print_feeds(cand_feeds, f"cand feeds, owner={ppss.web3_pp.owner_addrs}")

        feed: SubgraphFeed = ppss.predictoor_ss.get_feed_from_candidates(cand_feeds)
        if not feed:
            raise ValueError("No feeds found.")

        print_feeds({feed.address: feed}, "filtered feed")
        self.feed: SubgraphFeed = feed

        # set self.feed_contract. For both up/down. See submit_prediction_tx
        self.feed_contract: PredictoorContract = ppss.web3_pp.get_single_contract(
            feed.address
        )

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

        # within the time window to predict?
        if self.cur_epoch_s_left > self.epoch_s_thr:
            return
        if self.cur_epoch_s_left < self.s_cutoff:
            return

        if not self.check_balances():
            logger.error("Not enough balance, cancel prediction")
            return

        logger.info(self.status_str())

        # compute prediction; exit if no good
        submit_epoch, target_slot = self.cur_epoch, self.target_slot
        logger.info("Predict for time slot = %s...", self.target_slot)

        stake_up, stake_down = self.calc_stakes()
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
        return self.feed.seconds_per_epoch

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
    def up_addr(self) -> str:
        return self.web3_config_up.owner

    @property
    def down_addr(self) -> str:
        return self.web3_config_down.owner

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
        stake_up: Eth,
        stake_down: Eth,
        target_slot: UnixTimeS,  # a timestamp
    ):
        logger.info("Submit 'up' prediction tx to chain...")
        tx1 = self.submit_1prediction_tx(True, stake_up, target_slot)

        logger.info("Submit 'down' prediction tx to chain...")
        tx2 = self.submit_1prediction_tx(False, stake_down, target_slot)

        # handle errors
        if _tx_failed(tx1) or _tx_failed(tx2):
            s = "One or both txs failed. So, resubmit both with zero stake."
            s += f"\ntx1={tx1}\ntx2={tx2}"
            logger.warning(s)

            logger.info("Re-submit 'up' prediction tx to chain... (stake=0)")
            self.submit_1prediction_tx(True, Eth(1e-10), target_slot)
            logger.info("Re-submit 'down' prediction tx to chain... (stake=0)")
            self.submit_1prediction_tx(False, Eth(1e-10), target_slot)

    @enforce_types
    def submit_1prediction_tx(
        self,
        direction: bool,
        stake: Eth,  # in units of Eth
        target_slot: UnixTimeS,  # a timestamp
    ):
        web3_config = self._updown_web3_config(direction)
        self.feed_contract.web3_pp.set_web3_config(web3_config)
        self.feed_contract.set_token(self.feed_contract.web3_pp)

        tx = self.feed_contract.submit_prediction(
            direction,
            stake,
            target_slot,
            wait_for_receipt=True,
        )
        return tx

    def _updown_web3_config(self, direction: bool) -> Web3Config:
        """Returns the web3_config corresponding to up vs down direction"""
        if direction is True:
            return self.web3_config_up

        return self.web3_config_down

    @enforce_types
    def calc_stakes(self) -> Tuple[Eth, Eth]:
        """
        @return
          stake_up -- amt to stake up, in units of Eth
          stake_down -- amt to stake down, ""
        """
        approach = self.ppss.predictoor_ss.approach
        if approach == 1:
            return self.calc_stakes1()
        if approach == 2:
            return self.calc_stakes2()
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
    def check_balances(self) -> bool:
        min_OCEAN_bal = self.ppss.predictoor_ss.stake_amount.to_wei()
        min_ROSE_bal = Eth(1).to_wei()

        # TODO check manager balance here

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
