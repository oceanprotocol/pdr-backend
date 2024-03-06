
from enforce_typing import enforce_types
from matplotlib import gridspec
import matplotlib.pyplot as plt
import numpy as np
from numpy.random import random
from statsmodels.stats.proportion import proportion_confint

from pdr_backend.aimodel.plot_model import plot_model

FONTSIZE = 9

@enforce_types
class SimPlotState:
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
        self.plotted_before: bool = False
        plt.ion()
        plt.show()

    # pylint: disable=too-many-statements
    def make_plot(self, st, ppss, model, X_train, ybool_train, colnames):
        stake_amt = ppss.predictoor_ss.stake_amount.amt_eth

        fig = self.fig
        ax00, ax01 = self.ax00, self.ax01
        ax10, ax11, ax12 = self.ax10, self.ax11, self.ax12

        N = len(st.pdr_profits_OCEAN)
        N_done = len(self.x)  # what # points have been plotted previously

        # set x
        self.x = list(range(0, N))
        next_x = _slice(self.x, N_done, N)
        next_hx = [next_x[0], next_x[-1]]  # horizontal x

        # plot row 0, col 0: predictoor profit vs time
        y00 = list(np.cumsum(st.pdr_profits_OCEAN))
        next_y00 = _slice(y00, N_done, N)
        ax00.plot(next_x, next_y00, c="g")
        ax00.plot(next_hx, [0, 0], c="0.2", ls="--", lw=1)
        s = f"Predictoor profit vs time. Current:{y00[-1]:.2f} OCEAN"
        _set_title(ax00, s)
        if not self.plotted_before:
            ax00.set_ylabel("predictoor profit (OCEAN)", fontsize=FONTSIZE)
            ax00.set_xlabel("time", fontsize=FONTSIZE)
            _ylabel_on_right(ax00)
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
            _ylabel_on_right(ax01)
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
            _ylabel_on_right(ax10)
            ax10.margins(0.005, 0.05)

        # reusable profits scatterplot
        def _scatter_profits(ax, actor: str, denomin, mnp, mxp, st_profits):
            next_probs_up = _slice(st.probs_up, N_done, N)
            next_profits = _slice(st_profits, N_done, N)
            c = (random(), random(), random())  # random RGB color
            ax.scatter(next_probs_up, next_profits, color=c, s=1)
            avg = np.average(st_profits)
            s = f"{actor} profit distr'n. avg={avg:.2f} {denomin}"
            _set_title(ax, s)
            ax.plot([0.5, 0.5], [mnp, mxp], c="0.2", ls="-", lw=1)
            if not self.plotted_before:
                ax.plot([0.0, 1.0], [0, 0], c="0.2", ls="--", lw=1)
                _set_xlabel(ax, "prob(up)")
                _set_ylabel(ax, f"{actor} profit ({denomin})")
                _ylabel_on_right(ax)
                ax.margins(0.05, 0.05)

        # plot row 1, col 1: 1d scatter of predictoor profits
        mnp, mxp = -stake_amt, +stake_amt
        _scatter_profits(ax11, "pdr", "OCEAN", mnp, mxp, st.pdr_profits_OCEAN)

        # plot row 1, col 2: 1d scatter of trader profits
        mnp, mxp = min(st.trader_profits_USD), max(st.trader_profits_USD)
        _scatter_profits(ax12, "trader", "USD", mnp, mxp, st.trader_profits_USD)

        # final pieces
        HEIGHT = 7.5  # magic number
        WIDTH = int(HEIGHT * 3.2)  # magic number
        fig.set_size_inches(WIDTH, HEIGHT)
        fig.tight_layout(pad=0.5, h_pad=1.0, w_pad=1.0)
        plt.pause(0.001)
        self.plotted_before = True


def _shift_one_earlier(s: str):
    """eg 'binance:BTC/USDT:close:t-3' -> 'binance:BTC/USDT:close:t-2'"""
    val = int(s[-1])
    return s[:-1] + str(val - 1)


def _set_xlabel(ax, s: str):
    ax.set_xlabel(s, fontsize=FONTSIZE)


def _set_ylabel(ax, s: str):
    ax.set_ylabel(s, fontsize=FONTSIZE)


def _set_title(ax, s: str):
    ax.set_title(s, fontsize=FONTSIZE, fontweight="bold")


def _slice(a: list, N_done: int, N: int) -> list:
    return [a[i] for i in range(max(0, N_done - 1), N)]


def _ylabel_on_right(ax):
    ax.yaxis.tick_right()
    ax.yaxis.set_label_position("right")


def _del_lines(ax):
    for l in ax.lines:
        l.remove()
