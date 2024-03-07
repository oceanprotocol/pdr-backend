import copy
import logging
import os
from unittest.mock import Mock

from enforce_typing import enforce_types
import numpy as np
import polars as pl
from statsmodels.stats.proportion import proportion_confint

from pdr_backend.aimodel.aimodel_data_factory import AimodelDataFactory
from pdr_backend.aimodel.aimodel_factory import AimodelFactory
from pdr_backend.lake.ohlcv_data_factory import OhlcvDataFactory
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.sim.sim_state import SimState
from pdr_backend.sim.sim_plotter import SimPlotter
from pdr_backend.util.mathutil import classif_acc
from pdr_backend.util.time_types import UnixTimeMs

logger = logging.getLogger("sim_engine")


# pylint: disable=too-many-instance-attributes
class SimEngine:
    @enforce_types
    def __init__(self, ppss: PPSS):
        # preconditions
        predict_feed = ppss.predictoor_ss.feed

        # timeframe doesn't need to match
        assert (
            str(predict_feed.exchange),
            str(predict_feed.pair),
        ) in ppss.predictoor_ss.aimodel_ss.exchange_pair_tups

        self.ppss = ppss

        self.st = SimState(
            copy.copy(self.ppss.trader_ss.init_holdings),
        )

        if self.ppss.sim_ss.do_plot:
            n = self.ppss.predictoor_ss.aimodel_ss.n  # num input vars
            include_contour = n == 2
            self.sim_plotter = SimPlotter(self.ppss, self.st, include_contour)
        else:
            self.sim_plotter = Mock(spec=SimPlotter)

        self.logfile = ""

        self.exchange = self.ppss.predictoor_ss.feed.ccxt_exchange(
            mock=self.ppss.sim_ss.tradetype in ["histmock", "histmock"],
            exchange_params=self.ppss.sim_ss.exchange_params,
        )

    @property
    def tokcoin(self) -> str:
        """Return e.g. 'ETH'"""
        return self.ppss.predictoor_ss.base_str

    @property
    def usdcoin(self) -> str:
        """Return e.g. 'USDT'"""
        return self.ppss.predictoor_ss.quote_str

    @enforce_types
    def _init_loop_attributes(self):
        filebase = f"out_{UnixTimeMs.now()}.txt"
        self.logfile = os.path.join(self.ppss.sim_ss.log_dir, filebase)

        fh = logging.FileHandler(self.logfile)
        fh.setLevel(logging.INFO)
        logger.addHandler(fh)

        self.st.init_loop_attributes()

    @enforce_types
    def run(self):
        self._init_loop_attributes()
        logger.info("Start run")

        # main loop!
        f = OhlcvDataFactory(self.ppss.lake_ss)
        mergedohlcv_df = f.get_mergedohlcv_df()
        for test_i in range(self.ppss.sim_ss.test_n):
            self.run_one_iter(test_i, mergedohlcv_df)

        logger.info("Done all iters.")

        acc_train = np.average(self.st.accs_train)
        acc_test = classif_acc(self.st.ybools_testhat, self.st.ybools_test)
        logger.info("Final acc_train=%.5f, acc_test=%.5f", acc_train, acc_test)

    # pylint: disable=too-many-statements# pylint: disable=too-many-statements
    @enforce_types
    def run_one_iter(self, test_i: int, mergedohlcv_df: pl.DataFrame):
        ppss, pdr_ss = self.ppss, self.ppss.predictoor_ss
        stake_amt = pdr_ss.stake_amount.amt_eth
        others_stake = pdr_ss.others_stake.amt_eth
        revenue = pdr_ss.revenue.amt_eth
        trade_amt = ppss.trader_ss.buy_amt_usd.amt_eth

        testshift = ppss.sim_ss.test_n - test_i - 1  # eg [99, 98, .., 2, 1, 0]
        data_f = AimodelDataFactory(pdr_ss)
        X, ycont, x_df, _ = data_f.create_xy(
            mergedohlcv_df,
            testshift,
        )
        colnames = list(x_df.columns)

        st, fin = 0, X.shape[0] - 1
        X_train, X_test = X[st:fin, :], X[fin : fin + 1]
        ycont_train, ycont_test = ycont[st:fin], ycont[fin : fin + 1]

        curprice = ycont_train[-1]
        trueprice = ycont_test[-1]

        y_thr = curprice
        ybool = data_f.ycont_to_ytrue(ycont, y_thr)
        ybool_train, _ = ybool[st:fin], ybool[fin : fin + 1]

        model_f = AimodelFactory(pdr_ss.aimodel_ss)
        model = model_f.build(X_train, ybool_train)

        ybool_trainhat = model.predict_true(X_train)  # eg yhat=zhat[y-5]
        acc_train = classif_acc(ybool_train, ybool_trainhat)
        self.st.accs_train.append(acc_train)

        # current time
        recent_ut = UnixTimeMs(int(mergedohlcv_df["timestamp"].to_list()[-1]))
        ut = UnixTimeMs(recent_ut - testshift * pdr_ss.timeframe_ms)

        # predict price direction
        prob_up: float = model.predict_ptrue(X_test)[0]  # in [0.0, 1.0]
        pred_up: bool = model.predict_true(X_test)[0]  # True or False
        self.st.probs_up.append(prob_up)
        self.st.ybools_testhat.append(pred_up)

        # predictoor: (simulate) submit predictions with stake
        acct_up_profit = acct_down_profit = 0.0
        stake_up = stake_amt * prob_up
        stake_down = stake_amt * (1.0 - prob_up)
        acct_up_profit -= stake_up
        acct_down_profit -= stake_down

        # trader: enter the trading position
        usdcoin_holdings_before = self.st.holdings[self.usdcoin]
        if pred_up:  # buy; exit later by selling
            conf_up = (prob_up - 0.5) * 2.0  # to range [0,1]
            usdcoin_amt_send = trade_amt * conf_up
            tokcoin_amt_recd = self._buy(curprice, usdcoin_amt_send)
        else:  # sell; exit later by buying
            prob_down = 1.0 - prob_up
            conf_down = (prob_down - 0.5) * 2.0  # to range [0,1]
            target_usdcoin_amt_recd = trade_amt * conf_down
            p = self.ppss.trader_ss.fee_percent
            tokcoin_amt_send = target_usdcoin_amt_recd / curprice / (1 - p)
            self._sell(curprice, tokcoin_amt_send)

        # observe true price
        true_up = trueprice > curprice
        self.st.ybools_test.append(true_up)

        # trader: exit the trading position
        if pred_up:
            # we'd bought; so now sell
            self._sell(trueprice, tokcoin_amt_recd)
        else:
            # we'd sold, so buy back the same # tokcoins as we sold
            # (do *not* buy back the same # usdcoins! Not the same thing!)
            target_tokcoin_amt_recd = tokcoin_amt_send
            p = self.ppss.trader_ss.fee_percent
            usdcoin_amt_send = target_tokcoin_amt_recd * (1 - p) * trueprice
            tokcoin_amt_recd = self._buy(trueprice, usdcoin_amt_send)
        usdcoin_holdings_after = self.st.holdings[self.usdcoin]

        # track prediction
        pred_dir = "UP" if pred_up else "DN"
        true_dir = "UP" if true_up else "DN"
        correct = pred_dir == true_dir
        self.st.corrects.append(correct)

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
        self.st.pdr_profits_OCEAN.append(pdr_profit_OCEAN)

        # track trading profit
        trader_profit_USD = usdcoin_holdings_after - usdcoin_holdings_before
        self.st.trader_profits_USD.append(trader_profit_USD)

        # log
        n_correct, n_trials = sum(self.st.corrects), len(self.st.corrects)
        acc_est = float(n_correct) / n_trials
        acc_l, acc_u = proportion_confint(count=n_correct, nobs=n_trials)

        s = f"Iter #{test_i+1}/{ppss.sim_ss.test_n}: "
        s += f"ut={ut.pretty_timestr()[9:][:-10]}"

        s += f" prob_up={prob_up:.2f}"
        s += " predictoor profit = "
        s += f"{acct_up_profit:8.5f} up"
        s += f" + {acct_down_profit:8.5f} down"
        s += f" = {pdr_profit_OCEAN:8.5f} OCEAN"
        s += f" (cumulative {sum(self.st.pdr_profits_OCEAN):7.2f} OCEAN)"

        s += f". Correct: {n_correct:4d}/{n_trials:4d} "
        s += f"= {acc_est*100:.2f}%"
        s += f" [{acc_l*100:.2f}%, {acc_u*100:.2f}%]"

        s += f". trader profit = ${trader_profit_USD:9.4f}"
        s += f" (cumulative ${sum(self.st.trader_profits_USD):9.4f})"
        logger.info(s)

        # plot
        if self.do_plot(test_i, self.ppss.sim_ss.test_n):
            model_plot_args = (model, X_train, ybool_train, colnames)
            self.sim_plotter.do_plot(model_plot_args)

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
            self.ppss.predictoor_ss.pair_str, tokcoin_amt_recd
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
            self.ppss.predictoor_ss.pair_str, tokcoin_amt_send
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

    @enforce_types
    def do_plot(self, i: int, N: int):
        "Plot on this iteration Y/N?"
        if not self.ppss.sim_ss.do_plot:
            return False

        # don't plot first 5 iters -> not interesting
        # then plot the next 5 -> "stuff's happening!"
        # then plot every 5th iter, to balance "stuff's happening" w/ speed
        do_update = i >= 5 and (i < 10 or i % 5 == 0 or (i + 1) == N)
        if not do_update:
            return False

        return True
