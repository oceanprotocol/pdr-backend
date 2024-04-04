import copy
import logging
import os
from typing import Optional

import numpy as np
from pdr_backend.cli.predict_feeds import PredictFeed
import polars as pl

from enforce_typing import enforce_types
from sklearn.metrics import precision_recall_fscore_support
from statsmodels.stats.proportion import proportion_confint

from pdr_backend.aimodel.aimodel_data_factory import AimodelDataFactory
from pdr_backend.aimodel.aimodel_factory import AimodelFactory
from pdr_backend.aimodel.aimodel_plotdata import AimodelPlotdata
from pdr_backend.lake.ohlcv_data_factory import OhlcvDataFactory
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.sim.sim_plotter import SimPlotter
from pdr_backend.sim.sim_state import SimState
from pdr_backend.util.time_types import UnixTimeMs

logger = logging.getLogger("sim_engine")


# pylint: disable=too-many-instance-attributes
class SimEngine:
    @enforce_types
    # TODO Update simengine so that it takes a feed as argument in the constructor
    # And uses that feed for all the operations, instead of using the ppss object
    def __init__(self, ppss: PPSS, feed: PredictFeed, multi_id: Optional[str] = None):
        # preconditions
        predict_feeds = ppss.predictoor_ss.feeds

        # timeframe doesn't need to match
        for predict_feed in predict_feeds.feeds:
            assert (
                str(predict_feed.exchange),
                str(predict_feed.pair),
            ) in ppss.predictoor_ss.aimodel_ss.exchange_pair_tups

        self.ppss = ppss

        self.st = SimState(
            copy.copy(self.ppss.trader_ss.init_holdings),
        )

        self.sim_plotter = SimPlotter()

        self.logfile = ""

        self.exchanges = [
            feed.ccxt_exchange(
                mock=self.ppss.sim_ss.tradetype in ["histmock", "histmock"],
                exchange_params=self.ppss.sim_ss.exchange_params,
            )
            for feed in predict_feeds.feeds
        ]

        self.multi_id = multi_id

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

        self.sim_plotter.init_state()

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
        X, ycont, x_df, _ = data_f.create_xy(
            mergedohlcv_df,
            testshift,
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

        model_f = AimodelFactory(pdr_ss.aimodel_ss)
        model = model_f.build(X_train, ytrue_train)

        # current time
        recent_ut = UnixTimeMs(int(mergedohlcv_df["timestamp"].to_list()[-1]))
        ut = UnixTimeMs(recent_ut - testshift * pdr_ss.timeframe_ms)

        # predict price direction
        prob_up: float = model.predict_ptrue(X_test)[0]  # in [0.0, 1.0]
        pred_up: bool = prob_up > 0.5
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
        st.clm.update(acc_est, acc_l, acc_u, f1, precision, recall)

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

        # log
        s = f"Iter #{test_i+1}/{ppss.sim_ss.test_n}: "
        s += f"ut={ut.pretty_timestr()[9:][:-10]}"

        s += f" prob_up={prob_up:.2f}"
        s += " pdr profit = "
        s += f"{acct_up_profit:7.4f} up"
        s += f" + {acct_down_profit:7.4f} down"
        s += f" = {pdr_profit_OCEAN:7.4f} OCEAN"
        s += f" (cumul. {sum(st.pdr_profits_OCEAN):7.2f} OCEAN)"

        s += f". Acc={n_correct:4d}/{n_trials:4d} "
        s += f"= {acc_est*100:.2f}% [{acc_l*100:.2f}%, {acc_u*100:.2f}%]"
        s += f", prcsn={precision:.3f}, recall={recall:.3f}"
        s += f", f1={f1:.3f}"

        s += f". trader profit = ${trader_profit_USD:9.4f}"
        s += f" (cumul. ${sum(st.trader_profits_USD):9.4f})"
        logger.info(s)

        save_state, is_final_state = self.save_state(test_i, self.ppss.sim_ss.test_n)

        # temporarily we don't allow streamlit supervision of multisim runs
        if save_state and not self.multi_id:
            colnames = [_shift_one_earlier(colname) for colname in colnames]
            most_recent_x = X[-1, :]
            slicing_x = most_recent_x  # plot about the most recent x
            d = AimodelPlotdata(
                model,
                X_train,
                ytrue_train,
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
    def save_state(self, i: int, N: int):
        "Save state on this iteration Y/N?"
        if self.ppss.sim_ss.is_final_iter(i):
            return True, True

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
