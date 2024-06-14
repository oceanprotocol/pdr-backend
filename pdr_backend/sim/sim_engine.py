import copy
import logging
import os
import uuid
from typing import Optional

import numpy as np
import polars as pl
from enforce_typing import enforce_types
from sklearn.metrics import log_loss, precision_recall_fscore_support
from statsmodels.stats.proportion import proportion_confint

from pdr_backend.aimodel.aimodel import Aimodel
from pdr_backend.aimodel.aimodel_data_factory import AimodelDataFactory
from pdr_backend.aimodel.aimodel_factory import AimodelFactory
from pdr_backend.aimodel.aimodel_plotdata import AimodelPlotdata
from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_timeframe import ArgTimeframe
from pdr_backend.cli.predict_train_feedsets import PredictTrainFeedset
from pdr_backend.exchange.exchange_mgr import ExchangeMgr
from pdr_backend.lake.ohlcv_data_factory import OhlcvDataFactory
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.sim.sim_logger import SimLogLine
from pdr_backend.sim.sim_plotter import SimPlotter
from pdr_backend.sim.sim_state import SimState
from pdr_backend.util.time_types import UnixTimeMs

logger = logging.getLogger("sim_engine")


# pylint: disable=too-many-instance-attributes
class SimEngine:
    @enforce_types
    def __init__(
        self,
        ppss: PPSS,
        predict_train_feedset: PredictTrainFeedset,
        multi_id: Optional[str] = None,
    ):
        self.predict_train_feedset = predict_train_feedset
        assert isinstance(self.predict_feed, ArgFeed)
        assert isinstance(self.tokcoin, str)
        assert isinstance(self.usdcoin, str)

        self.ppss = ppss

        # can be disabled by calling disable_realtime_state()
        self.do_state_updates = True

        self.st = SimState(
            copy.copy(self.ppss.trader_ss.init_holdings),
        )

        self.sim_plotter = SimPlotter()

        self.logfile = ""

        mock = self.ppss.sim_ss.tradetype in ["histmock"]
        exchange_mgr = ExchangeMgr(self.ppss.exchange_mgr_ss)
        self.exchange = exchange_mgr.exchange(
            "mock" if mock else ppss.predictoor_ss.exchange_str,
        )

        if multi_id:
            self.multi_id = multi_id
        else:
            self.multi_id = str(uuid.uuid4())

        self.crt_trained_model: Optional[Aimodel] = None

    @property
    def predict_feed(self) -> ArgFeed:
        return self.predict_train_feedset.predict

    @property
    def tokcoin(self) -> str:
        """Return e.g. 'ETH'"""
        return self.predict_feed.pair.base_str

    @property
    def usdcoin(self) -> str:
        """Return e.g. 'USDT'"""
        return self.predict_feed.pair.quote_str

    @enforce_types
    def _init_loop_attributes(self):
        filebase = f"out_{UnixTimeMs.now()}.txt"
        self.logfile = os.path.join(self.ppss.sim_ss.log_dir, filebase)

        fh = logging.FileHandler(self.logfile)
        fh.setLevel(logging.INFO)
        logger.addHandler(fh)

        self.st.init_loop_attributes()
        logger.info("Initialize plot data.")
        self.sim_plotter.init_state(self.multi_id)

    @enforce_types
    def run(self):
        logger.info("Start run")
        self._init_loop_attributes()

        # main loop!
        f = OhlcvDataFactory(self.ppss.lake_ss)
        mergedohlcv_df = f.get_mergedohlcv_df()

        for test_i in range(self.ppss.sim_ss.test_n):
            self.run_one_iter(test_i, mergedohlcv_df)

        logger.info("Done all iters.")

    # pylint: disable=too-many-statements# pylint: disable=too-many-statements
    @enforce_types
    def run_one_iter(self, test_i: int, mergedohlcv_df: pl.DataFrame):
        ppss, pdr_ss, st = self.ppss, self.ppss.predictoor_ss, self.st
        stake_amt = pdr_ss.stake_amount.amt_eth
        others_stake = pdr_ss.others_stake.amt_eth
        revenue = pdr_ss.revenue.amt_eth
        trade_amt = ppss.trader_ss.buy_amt_usd.amt_eth

        testshift = ppss.sim_ss.test_n - test_i - 1  # eg [99, 98, .., 2, 1, 0]
        data_f = AimodelDataFactory(pdr_ss)  # type: ignore[arg-type]
        predict_feed = self.predict_train_feedset.predict
        train_feeds = self.predict_train_feedset.train_on
        X, ycont, x_df, _ = data_f.create_xy(
            mergedohlcv_df,
            testshift,
            predict_feed,
            train_feeds,
        )
        colnames = list(x_df.columns)

        st_, fin = 0, X.shape[0] - 1
        X_train, X_test = X[st_:fin, :], X[fin : fin + 1]
        ycont_train, ycont_test = ycont[st_:fin], ycont[fin : fin + 1]

        curprice = ycont_train[-1]
        trueprice = ycont_test[-1]

        y_thr = curprice
        ytrue = data_f.ycont_to_ytrue(ycont, y_thr)
        ytrue_train, _ = ytrue[st_:fin], ytrue[fin : fin + 1]

        if self.st.iter_number % pdr_ss.aimodel_ss.train_every_n_epochs == 0:
            model_f = AimodelFactory(pdr_ss.aimodel_ss)
            model = model_f.build(X_train, ytrue_train, ycont_train, y_thr)
            self.crt_trained_model = model
        else:
            assert self.crt_trained_model is not None
            model = self.crt_trained_model

        # current time
        recent_ut = UnixTimeMs(int(mergedohlcv_df["timestamp"].to_list()[-1]))
        timeframe: ArgTimeframe = predict_feed.timeframe  # type: ignore
        ut = UnixTimeMs(recent_ut - testshift * timeframe.ms)

        # predict price direction
        prob_up: float = model.predict_ptrue(X_test)[0]  # in [0.0, 1.0]
        prob_down: float = 1.0 - prob_up
        conf_up = (prob_up - 0.5) * 2.0  # to range [0,1]
        conf_down = (prob_down - 0.5) * 2.0  # to range [0,1]
        conf_threshold = self.ppss.trader_ss.sim_confidence_threshold
        pred_up: bool = prob_up > 0.5 and conf_up > conf_threshold
        pred_down: bool = prob_up < 0.5 and conf_down > conf_threshold
        st.probs_up.append(prob_up)

        # predictoor: (simulate) submit predictions with stake
        acct_up_profit = acct_down_profit = 0.0
        stake_up = stake_amt * prob_up
        stake_down = stake_amt * (1.0 - prob_up)
        acct_up_profit -= stake_up
        acct_down_profit -= stake_down

        # trader: enter the trading position
        usdcoin_holdings_before = st.holdings[self.usdcoin]
        if pred_up:  # buy; exit later by selling
            usdcoin_amt_send = trade_amt * conf_up
            tokcoin_amt_recd = self._buy(curprice, usdcoin_amt_send)
        elif pred_down:  # sell; exit later by buying
            target_usdcoin_amt_recd = trade_amt * conf_down
            p = self.ppss.trader_ss.fee_percent
            tokcoin_amt_send = target_usdcoin_amt_recd / curprice / (1 - p)
            self._sell(curprice, tokcoin_amt_send)

        # observe true price
        true_up = trueprice > curprice
        st.ytrues.append(true_up)

        # update classifier metrics
        n_correct = sum(np.array(st.ytrues) == np.array(st.ytrues_hat))
        n_trials = len(st.ytrues)
        acc_est = n_correct / n_trials
        acc_l, acc_u = proportion_confint(count=n_correct, nobs=n_trials)
        (precision, recall, f1, _) = precision_recall_fscore_support(
            st.ytrues,
            st.ytrues_hat,
            average="binary",
            zero_division=0.0,
        )
        if min(st.ytrues) == max(st.ytrues):
            loss = 3.0
        else:
            loss = log_loss(st.ytrues, st.probs_up)
        yerr = 0.0
        if model.do_regr:
            predprice = model.predict_ycont(X_test)[0]
            yerr = trueprice - predprice
        st.aim.update(acc_est, acc_l, acc_u, f1, precision, recall, loss, yerr)

        # trader: exit the trading position
        if pred_up:
            # we'd bought; so now sell
            self._sell(trueprice, tokcoin_amt_recd)
        elif pred_down:
            # we'd sold, so buy back the same # tokcoins as we sold
            # (do *not* buy back the same # usdcoins! Not the same thing!)
            target_tokcoin_amt_recd = tokcoin_amt_send
            p = self.ppss.trader_ss.fee_percent
            usdcoin_amt_send = target_tokcoin_amt_recd * trueprice / (1 - p)
            tokcoin_amt_recd = self._buy(trueprice, usdcoin_amt_send)
        usdcoin_holdings_after = st.holdings[self.usdcoin]

        # track predictoor profit
        tot_stake = others_stake + stake_amt
        others_stake_correct = others_stake * pdr_ss.others_accuracy
        if true_up:
            tot_stake_correct = others_stake_correct + stake_up
            percent_to_me = stake_up / tot_stake_correct
            acct_up_profit += (revenue + tot_stake) * percent_to_me
        else:
            tot_stake_correct = others_stake_correct + stake_down
            percent_to_me = stake_down / tot_stake_correct
            acct_down_profit += (revenue + tot_stake) * percent_to_me
        pdr_profit_OCEAN = acct_up_profit + acct_down_profit
        st.pdr_profits_OCEAN.append(pdr_profit_OCEAN)

        # track trading profit
        trader_profit_USD = usdcoin_holdings_after - usdcoin_holdings_before
        st.trader_profits_USD.append(trader_profit_USD)

        SimLogLine(ppss, st, test_i, ut, acct_up_profit, acct_down_profit).log_line()

        save_state, is_final_state = self.save_state(test_i, self.ppss.sim_ss.test_n)

        if save_state:
            colnames = [_shift_one_earlier(colname) for colname in colnames]
            most_recent_x = X[-1, :]
            slicing_x = most_recent_x  # plot about the most recent x
            d = AimodelPlotdata(
                model,
                X_train,
                ytrue_train,
                ycont_train,
                y_thr,
                colnames,
                slicing_x,
            )
            self.st.iter_number = test_i
            self.sim_plotter.save_state(self.st, d, is_final_state)

    @enforce_types
    def _buy(self, price: float, usdcoin_amt_send: float) -> float:
        """
        @description
          Buy tokcoin with usdcoin. That is, swap usdcoin for tokcoin.

        @arguments
          price -- amt of usdcoin per token
          usdcoin_amt_send -- # usdcoins to send. It sends less if have less
        @return
          tokcoin_amt_recd -- # tokcoins received.
        """
        usdcoin_amt_send = min(usdcoin_amt_send, self.st.holdings[self.usdcoin])
        self.st.holdings[self.usdcoin] -= usdcoin_amt_send

        p = self.ppss.trader_ss.fee_percent
        usdcoin_amt_fee = usdcoin_amt_send * p
        tokcoin_amt_recd = usdcoin_amt_send * (1 - p) / price
        self.st.holdings[self.tokcoin] += tokcoin_amt_recd

        self.exchange.create_market_buy_order(
            str(self.predict_feed.pair), tokcoin_amt_recd
        )

        logger.info(
            "TX: BUY : send %8.2f %s, receive %8.2f %s, fee = %8.4f %s",
            usdcoin_amt_send,
            self.usdcoin,
            tokcoin_amt_recd,
            self.tokcoin,
            usdcoin_amt_fee,
            self.usdcoin,
        )

        return tokcoin_amt_recd

    @enforce_types
    def _sell(self, price: float, tokcoin_amt_send: float) -> float:
        """
        @description
          Sell tokcoin for usdcoin. That is, swap tokcoin for usdcoin.

        @arguments
          price -- amt of usdcoin per token
          tokcoin_amt_send -- # tokcoins to send. It sends less if have less

        @return
          usdcoin_amt_recd -- # usdcoins received
        """
        tokcoin_amt_send = min(tokcoin_amt_send, self.st.holdings[self.tokcoin])
        self.st.holdings[self.tokcoin] -= tokcoin_amt_send

        p = self.ppss.trader_ss.fee_percent
        usdcoin_amt_fee = tokcoin_amt_send * p * price
        usdcoin_amt_recd = tokcoin_amt_send * (1 - p) * price
        self.st.holdings[self.usdcoin] += usdcoin_amt_recd

        self.exchange.create_market_sell_order(
            str(self.predict_feed.pair), tokcoin_amt_send
        )

        logger.info(
            "TX: SELL: send %8.2f %s, receive %8.2f %s, fee = %8.4f %s",
            tokcoin_amt_send,
            self.tokcoin,
            usdcoin_amt_recd,
            self.usdcoin,
            usdcoin_amt_fee,
            self.usdcoin,
        )

        return usdcoin_amt_recd

    def disable_realtime_state(self):
        self.do_state_updates = False

    @enforce_types
    def save_state(self, i: int, N: int):
        "Save state on this iteration Y/N?"
        if self.ppss.sim_ss.is_final_iter(i):
            return True, True

        # don't save if disabled
        if not self.do_state_updates:
            return False, False

        # don't save first 5 iters -> not interesting
        # then save the next 5 -> "stuff's happening!"
        # then save every 5th iter, to balance "stuff's happening" w/ speed
        do_update = i >= 5 and (i < 10 or i % 5 == 0 or (i + 1) == N)
        if not do_update:
            return False, False

        return True, False


@enforce_types
def _shift_one_earlier(s: str):
    """eg 'binance:BTC/USDT:close:t-3' -> 'binance:BTC/USDT:close:t-2'"""
    val = int(s[-1])
    return s[:-1] + str(val - 1)
