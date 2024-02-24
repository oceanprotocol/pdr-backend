import copy
import logging
import os
from typing import Dict, List, Union

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import polars as pl
from enforce_typing import enforce_types
from statsmodels.stats.proportion import proportion_confint

from pdr_backend.aimodel.plot_model import plot_model
from pdr_backend.aimodel.aimodel_data_factory import AimodelDataFactory
from pdr_backend.aimodel.aimodel_factory import AimodelFactory
from pdr_backend.lake.ohlcv_data_factory import OhlcvDataFactory
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.util.mathutil import classif_acc
from pdr_backend.util.time_types import UnixTimeMs

logger = logging.getLogger("sim_engine")
FONTSIZE = 9


# pylint: disable=too-many-instance-attributes
class SimEngineState:
    def __init__(self, init_holdings: Dict[str, Union[int, float]]):
        self.holdings: dict = init_holdings
        self.init_loop_attributes()

    def init_loop_attributes(self):
        self.accs_train: List[float] = []
        self.ybools_test: List[float] = []
        self.ybools_testhat: List[float] = []
        self.corrects: List[bool] = []
        self.trader_profits_USD: List[float] = []
        self.predictoor_profits_OCEAN: List[float] = []


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

        self.st = SimEngineState(
            copy.copy(self.ppss.trader_ss.init_holdings),
        )

        self.plot_state = None
        if self.ppss.sim_ss.do_plot:
            n = self.ppss.predictoor_ss.aimodel_ss.n  # num input vars
            include_contour = n == 2
            self.plot_state = PlotState(include_contour)

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

        testshift = ppss.sim_ss.test_n - test_i - 1  # eg [99, 98, .., 2, 1, 0]
        model_data_factory = AimodelDataFactory(pdr_ss)
        X, ycont, x_df, _ = model_data_factory.create_xy(
            mergedohlcv_df,
            testshift,
        )
        colnames = [col for col in x_df.columns]

        st, fin = 0, X.shape[0] - 1
        X_train, X_test = X[st:fin, :], X[fin : fin + 1]
        ycont_train, ycont_test = ycont[st:fin], ycont[fin : fin + 1]

        curprice: float = ycont_train[-1]
        trueprice: float = ycont_test[-1]

        y_thr: float = curprice
        ybool = model_data_factory.ycont_to_ytrue(ycont, y_thr)
        ybool_train, ybool_test = ybool[st:fin], ybool[fin : fin + 1]

        aimodel_factory = AimodelFactory(pdr_ss.aimodel_ss)
        model = aimodel_factory.build(X_train, ybool_train)

        ybool_trainhat = model.predict_true(X_train)  # eg yhat=zhat[y-5]
        acc_train = classif_acc(ybool_train, ybool_trainhat)
        self.st.accs_train.append(acc_train)

        # current time
        recent_ut = UnixTimeMs(int(mergedohlcv_df["timestamp"].to_list()[-1]))
        ut = UnixTimeMs(recent_ut - testshift * pdr_ss.timeframe_ms)

        # predict price direction
        prob_up: float = model.predict_ptrue(X_test)[0]  # in [0.0, 1.0]
        pred_up: bool = model.predict_true(X_test)[0]  # True or False
        self.st.ybools_testhat.append(pred_up)

        # predictoor: (simulate) submit predictions
        stake_up = prob_up * pdr_ss.stake_amount
        stake_down = (1.0 - prob_up) * pdr_ss.stake_amount

        # trader: enter the trading position
        usdcoin_holdings_before = self.st.holdings[self.usdcoin]
        if pred_up:  # buy; exit later by selling
            conf_up = (prob_up - 0.5) * 2.0  # to range [0,1]
            buy_amt_usd = conf_up * ppss.trader_ss.buy_amt_usd
            usdcoin_amt_sent = buy_amt_usd
            tokcoin_amt_recd = self._buy(curprice, usdcoin_amt_sent)
        else:  # sell; exit later by buying
            prob_down = 1.0 - prob_up
            conf_down = (prob_down - 0.5) * 2.0  # to range [0,1]
            sell_amt_usd = conf_down * ppss.trader_ss.buy_amt_usd
            p = self.ppss.trader_ss.fee_percent
            tokcoin_amt_sent = sell_amt_usd / curprice / (1 - p)
            usdcoin_amt_recd = self._sell(curprice, tokcoin_amt_sent)

        # observe true price
        true_up = trueprice > curprice
        self.st.ybools_test.append(true_up)

        # trader: exit the trading position
        if pred_up:  # we'd bought; so now sell
            self._sell(trueprice, tokcoin_amt_sell=tokcoin_amt_recd)
        else:  # we'd sold, so now buy back
            self._buy(trueprice, usdcoin_amt_spend=usdcoin_amt_recd)

        usdcoin_holdings_after = self.st.holdings[self.usdcoin]

        # track prediction
        pred_dir = "UP" if pred_up else "DN"
        true_dir = "UP" if true_up else "DN"
        correct = pred_dir == true_dir
        correct_s = "Y" if correct else "N"
        self.st.corrects.append(correct)

        # track predictoor profit
        others_stake_correct = pdr_ss.others_accuracy * pdr_ss.others_stake
        others_stake_wrong = (1 - pdr_ss.others_accuracy) * pdr_ss.others_stake
        if true_up:
            tot_stake_correct = others_stake_correct + stake_up
            percent_to_me = stake_up / tot_stake_correct
            acct_up_profit = percent_to_me * (pdr_ss.revenue + others_stake_wrong)
            acct_down_profit = -stake_down
        else:
            tot_stake_correct = others_stake_correct + stake_down
            percent_to_me = stake_down / tot_stake_correct
            acct_up_profit = -stake_up
            acct_down_profit = percent_to_me * (pdr_ss.revenue + others_stake_wrong)
        predictoor_profit_OCEAN = acct_up_profit + acct_down_profit
        self.st.predictoor_profits_OCEAN.append(predictoor_profit_OCEAN)

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
        s += f" = {predictoor_profit_OCEAN:8.5f} OCEAN"
        s += f" (cumulative {sum(self.st.predictoor_profits_OCEAN):7.2f} OCEAN)"

        s += f". Correct: {n_correct:4d}/{n_trials:4d} "
        s += f"= {acc_est*100:.2f}%"
        s += f" [{acc_l*100:.2f}%, {acc_u*100:.2f}%]"

        s += f". trader profit = ${trader_profit_USD:9.4f}"
        s += f" (cumulative ${sum(self.st.trader_profits_USD):9.4f})"
        logger.info(s)

        # plot
        if self.do_plot(test_i, self.ppss.sim_ss.test_n):
            self.plot_state.make_plot(  # type: ignore[union-attr]
                self.st,
                model,
                X_train,
                ybool_train,
                colnames,
            )

    @enforce_types
    def _buy(self, price: float, usdcoin_amt_spend: float) -> float:
        """
        @description
          Buy tokcoin with usdcoin

        @arguments
          price -- amt of usdcoin per token
          usdcoin_amt_spend -- amount to spend, in usdcoin; spend less if have less
        @return
          tokcoin_amt_recd --
        """
        # simulate buy
        usdcoin_amt_sent = min(usdcoin_amt_spend, self.st.holdings[self.usdcoin])
        self.st.holdings[self.usdcoin] -= usdcoin_amt_sent

        p = self.ppss.trader_ss.fee_percent
        usdcoin_amt_fee = p * usdcoin_amt_sent
        tokcoin_amt_recd = (1 - p) * usdcoin_amt_sent / price
        self.st.holdings[self.tokcoin] += tokcoin_amt_recd

        self.exchange.create_market_buy_order(
            self.ppss.predictoor_ss.pair_str, tokcoin_amt_recd
        )

        logger.info(
            "TX: BUY : send %8.2f %s, receive %8.2f %s, fee = %8.4f %s",
            usdcoin_amt_sent,
            self.usdcoin,
            tokcoin_amt_recd,
            self.tokcoin,
            usdcoin_amt_fee,
            self.usdcoin,
        )

        return tokcoin_amt_recd

    @enforce_types
    def _sell(self, price: float, tokcoin_amt_sell: float) -> float:
        """
        @description
          Sell tokcoin for usdcoin

        @arguments
          price -- amt of usdcoin per token
          tokcoin_amt_sell -- how much of coin to sell, in tokcoin

        @return
          usdcoin_amt_recd -- usdcoin amt received
        """
        tokcoin_amt_sent = tokcoin_amt_sell
        self.st.holdings[self.tokcoin] -= tokcoin_amt_sent

        p = self.ppss.trader_ss.fee_percent
        usdcoin_amt_fee = p * tokcoin_amt_sent * price
        usdcoin_amt_recd = (1 - p) * tokcoin_amt_sent * price
        self.st.holdings[self.usdcoin] += usdcoin_amt_recd

        self.exchange.create_market_sell_order(
            self.ppss.predictoor_ss.pair_str, tokcoin_amt_sent
        )

        logger.info(
            "TX: SELL: send %8.2f %s, receive %8.2f %s, fee = %8.4f %s",
            tokcoin_amt_sent,
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


@enforce_types
class PlotState:
    def __init__(self, include_contour: bool):
        self.include_contour = include_contour

        fig = plt.figure()
        self.fig = fig

        if include_contour:
            gs = gridspec.GridSpec(2, 4, width_ratios=[5, 1, 1, 5])
        else:
            gs = gridspec.GridSpec(2, 3, width_ratios=[5, 1, 1])

        self.ax00 = fig.add_subplot(gs[0, 0])
        self.ax01 = fig.add_subplot(gs[0, 1:3])
        self.ax10 = fig.add_subplot(gs[1, 0])
        self.ax11 = fig.add_subplot(gs[1, 1])
        self.ax12 = fig.add_subplot(gs[1, 2])
        if include_contour:
            self.ax03 = fig.add_subplot(gs[:, 3])

        self.x: List[float] = []
        self.y01_est: List[float] = []
        self.y01_l: List[float] = []
        self.y01_u: List[float] = []
        self.jitter: List[float] = []
        self.plotted_before: bool = False
        plt.ion()
        plt.show()

    # pylint: disable=too-many-statements
    def make_plot(self, st, model, X_train, ybool_train, colnames):
        fig = self.fig
        ax00, ax01 = self.ax00, self.ax01
        ax10, ax11, ax12 = self.ax10, self.ax11, self.ax12

        N = len(st.predictoor_profits_OCEAN)
        N_done = len(self.x)  # what # points have been plotted previously

        # set x
        self.x = list(range(0, N))
        next_x = _slice(self.x, N_done, N)
        next_hx = [next_x[0], next_x[-1]]  # horizontal x

        # plot row 0, col 0: predictoor profit vs time
        y00 = list(np.cumsum(st.predictoor_profits_OCEAN))
        next_y00 = _slice(y00, N_done, N)
        ax00.plot(next_x, next_y00, c="g")
        ax00.plot(next_hx, [0, 0], c="0.2", ls="--", lw=1)
        s = f"Predictoor profit vs time. Current:{y00[-1]:.2f} OCEAN"
        _set_title(ax00, s)
        if not self.plotted_before:
            ax00.set_ylabel("predictoor profit (OCEAN)", fontsize=FONTSIZE)
            ax00.set_xlabel("time", fontsize=FONTSIZE)
            _label_on_right(ax00)
            ax00.margins(0.005, 0.05)

        # plot row 0, col 1: % correct vs time
        for i in range(N_done, N):
            n_correct = sum(st.corrects[: i + 1])
            n_trials = len(st.corrects[: i + 1])
            l, u = proportion_confint(count=n_correct, nobs=n_trials)
            self.y01_est.append(n_correct / n_trials * 100)
            self.y01_l.append(l * 100)
            self.y01_u.append(u * 100)
        next_y01_est = _slice(self.y01_est, N_done, N)
        next_y01_l = _slice(self.y01_l, N_done, N)
        next_y01_u = _slice(self.y01_u, N_done, N)

        ax01.plot(next_x, next_y01_est, "green")
        ax01.fill_between(next_x, next_y01_l, next_y01_u, color="0.9")
        ax01.plot(next_hx, [50, 50], c="0.2", ls="--", lw=1)
        ax01.set_ylim(bottom=40, top=60)
        now_s = f"{self.y01_est[-1]:.2f}% "
        now_s += f"[{self.y01_l[-1]:.2f}%, {self.y01_u[-1]:.2f}%]"
        _set_title(ax01, f"% correct vs time. Current: {now_s}")
        if not self.plotted_before:
            ax01.set_xlabel("time", fontsize=FONTSIZE)
            ax01.set_ylabel("% correct", fontsize=FONTSIZE)
            _label_on_right(ax01)
            ax01.margins(0.01, 0.01)

        # plot row 0, col 2: model contour
        if self.include_contour:
            ax03 = self.ax03
            labels = tuple([_shift_one_earlier(colname) for colname in colnames])
            plot_model(model, X_train, ybool_train, labels, (fig, ax03))
            if not self.plotted_before:
                ax03.margins(0.01, 0.01)

        # plot row 1, col 0: trader profit vs time
        y10 = list(np.cumsum(st.trader_profits_USD))
        next_y10 = _slice(y10, N_done, N)
        ax10.plot(next_x, next_y10, c="b")
        ax10.plot(next_hx, [0, 0], c="0.2", ls="--", lw=1)
        _set_title(ax10, f"Trader profit vs time. Current: ${y10[-1]:.2f}")
        if not self.plotted_before:
            ax10.set_xlabel("time", fontsize=FONTSIZE)
            ax10.set_ylabel("trader profit (USD)", fontsize=FONTSIZE)
            _label_on_right(ax10)
            ax10.margins(0.005, 0.05)

        # reusable profits scatterplot
        def _scatter_profits(ax, actor_name: str, denomin, st_profits):
            while len(self.jitter) < N:
                self.jitter.append(np.random.uniform())
            next_jitter = _slice(self.jitter, N_done, N)
            next_profits = _slice(st_profits, N_done, N)
            ax.scatter(next_jitter, next_profits, c="b", s=1)
            avg = np.average(st_profits)
            s = f"{actor_name} profit distr'n. avg={avg:.2f} {denomin}"
            _set_title(ax, s)
            if not self.plotted_before:
                buf = 1.0
                ax.plot([0 - buf, 1 + buf], [0, 0], c="0.2", ls="--", lw=1)
                _set_ylabel(ax, f"{actor_name} profit ({denomin})")
                _label_on_right(ax)
                plt.tick_params(bottom=False, labelbottom=False)
                ax.margins(0.05, 0.05)

        # plot row 1, col 1: 1d scatter of predictoor profits
        _scatter_profits(
            ax11,
            "pdr",
            "OCEAN",
            st.predictoor_profits_OCEAN,
        )

        # plot row 1, col 2: 1d scatter of trader profits
        _scatter_profits(ax12, "trader", "USD", st.trader_profits_USD)

        # final pieces
        HEIGHT = 7.5  # magic number
        WIDTH = int(HEIGHT * 3.2)  # magic number
        fig.set_size_inches(WIDTH, HEIGHT)
        fig.tight_layout(pad=0.5, h_pad=1.0, w_pad=1.0)
        plt.pause(0.001)
        self.plotted_before = True

        # import pdb; pdb.set_trace()


def _shift_one_earlier(s: str):
    """eg 'binance:BTC/USDT:close:t-3' -> 'binance:BTC/USDT:close:t-2'"""
    val = int(s[-1])
    return s[:-1] + str(val - 1)


def _set_ylabel(ax, s: str):
    ax.set_ylabel(s, fontsize=FONTSIZE)


def _set_title(ax, s: str):
    ax.set_title(s, fontsize=FONTSIZE, fontweight="bold")


def _slice(a: list, N_done: int, N: int) -> list:
    return [a[i] for i in range(max(0, N_done - 1), N)]


def _label_on_right(ax):
    ax.yaxis.tick_right()
    ax.yaxis.set_label_position("right")


def _del_lines(ax):
    for l in ax.lines:
        l.remove()
