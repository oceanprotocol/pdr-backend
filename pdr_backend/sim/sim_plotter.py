from typing import List

from enforce_typing import enforce_types
from matplotlib import gridspec
import matplotlib.pyplot as plt
import numpy as np
from numpy.random import random
from statsmodels.stats.proportion import proportion_confint

from pdr_backend.aimodel.aimodel_plotdata import AimodelPlotdata
from pdr_backend.aimodel.aimodel_plotter import (
    plot_aimodel_response,
    plot_aimodel_varimps,
)
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.sim.sim_state import SimState
from pdr_backend.util.constants import FONTSIZE

HEIGHT = 7.5
WIDTH = int(HEIGHT * 3.2)


# pylint: disable=too-many-instance-attributes
class SimPlotter:
    @enforce_types
    def __init__(
        self,
        ppss: PPSS,
        st: SimState,
    ):
        # engine state, ss
        self.st = st
        self.ppss = ppss

        # so labels are above lines. Must be before figure()
        plt.rcParams["axes.axisbelow"] = False

        # figure, subplots
        fig = plt.figure()
        self.fig = fig

        gs = gridspec.GridSpec(2, 6, width_ratios=[5, 1, 1, 0.6, 2, 3])

        self.ax_pdr_profit_vs_time = fig.add_subplot(gs[0, 0])
        self.ax_trader_profit_vs_time = fig.add_subplot(gs[1, 0])

        self.ax_accuracy_vs_time = fig.add_subplot(gs[0, 1:3])
        self.ax_pdr_profit_vs_ptrue = fig.add_subplot(gs[1, 1])
        self.ax_trader_profit_vs_ptrue = fig.add_subplot(gs[1, 2])

        # col 3 is empty, for overflow of aimodel_varimps's y-axis labels
        self.ax_aimodel_varimps = fig.add_subplot(gs[:, 4])

        self.ax_aimodel_response = fig.add_subplot(gs[:, 5])

        # attributes to help update plots' state quickly
        self.N: int = 0
        self.N_done: int = 0
        self.x: List[float] = []

        self.y01_est: List[float] = []
        self.y01_l: List[float] = []
        self.y01_u: List[float] = []
        self.plotted_before: bool = False

        # push plot to screen
        plt.ion()
        plt.show()

    # pylint: disable=too-many-statements
    @enforce_types
    def make_plot(self, aimodel_plotdata: AimodelPlotdata):
        """
        @description
          Create / update whole plot, with many subplots
        """
        # update N, N_done, x. **Update x only after updating N, N_done!**
        self.N = len(self.st.pdr_profits_OCEAN)
        self.N_done = len(self.x)  # what # points have been plotted previously
        self.x = list(range(0, self.N))

        # main work: create/update subplots
        self._plot_pdr_profit_vs_time()
        self._plot_trader_profit_vs_time()

        self._plot_accuracy_vs_time()
        self._plot_pdr_profit_vs_ptrue()
        self._plot_trader_profit_vs_ptrue()

        self._plot_aimodel_varimps(aimodel_plotdata)
        self._plot_aimodel_response(aimodel_plotdata)

        # final pieces
        self.fig.set_size_inches(WIDTH, HEIGHT)
        self.fig.tight_layout(pad=0.5, h_pad=1.0, w_pad=1.0)
        plt.subplots_adjust(wspace=0.3)
        plt.pause(0.001)
        self.plotted_before = True

    @property
    def next_x(self) -> List[float]:
        return _slice(self.x, self.N_done, self.N)

    @property
    def next_hx(self) -> List[float]:
        """horizontal x"""
        return [self.next_x[0], self.next_x[-1]]

    @enforce_types
    def _plot_pdr_profit_vs_time(self):
        ax = self.ax_pdr_profit_vs_time
        y00 = list(np.cumsum(self.st.pdr_profits_OCEAN))
        next_y00 = _slice(y00, self.N_done, self.N)
        ax.plot(self.next_x, next_y00, c="g")
        ax.plot(self.next_hx, [0, 0], c="0.2", ls="--", lw=1)
        s = f"Predictoor profit vs time. Current:{y00[-1]:.2f} OCEAN"
        _set_title(ax, s)
        if not self.plotted_before:
            ax.set_ylabel("predictoor profit (OCEAN)", fontsize=FONTSIZE)
            ax.set_xlabel("time", fontsize=FONTSIZE)
            _ylabel_on_right(ax)
            ax.margins(0.005, 0.05)

    @enforce_types
    def _plot_trader_profit_vs_time(self):
        ax = self.ax_trader_profit_vs_time
        y10 = list(np.cumsum(self.st.trader_profits_USD))
        next_y10 = _slice(y10, self.N_done, self.N)
        ax.plot(self.next_x, next_y10, c="b")
        ax.plot(self.next_hx, [0, 0], c="0.2", ls="--", lw=1)
        _set_title(ax, f"Trader profit vs time. Current: ${y10[-1]:.2f}")
        if not self.plotted_before:
            ax.set_xlabel("time", fontsize=FONTSIZE)
            ax.set_ylabel("trader profit (USD)", fontsize=FONTSIZE)
            _ylabel_on_right(ax)
            ax.margins(0.005, 0.05)

    @enforce_types
    def _plot_accuracy_vs_time(self):
        ax = self.ax_accuracy_vs_time
        for i in range(self.N_done, self.N):
            n_correct = sum(self.st.corrects[: i + 1])
            n_trials = len(self.st.corrects[: i + 1])
            l, u = proportion_confint(count=n_correct, nobs=n_trials)
            self.y01_est.append(n_correct / n_trials * 100)
            self.y01_l.append(l * 100)
            self.y01_u.append(u * 100)
        next_y01_est = _slice(self.y01_est, self.N_done, self.N)
        next_y01_l = _slice(self.y01_l, self.N_done, self.N)
        next_y01_u = _slice(self.y01_u, self.N_done, self.N)

        ax.plot(self.next_x, next_y01_est, "green")
        ax.fill_between(self.next_x, next_y01_l, next_y01_u, color="0.9")
        ax.plot(self.next_hx, [50, 50], c="0.2", ls="--", lw=1)
        ax.set_ylim(bottom=40, top=60)
        now_s = f"{self.y01_est[-1]:.2f}% "
        now_s += f"[{self.y01_l[-1]:.2f}%, {self.y01_u[-1]:.2f}%]"
        _set_title(ax, f"% correct vs time. Current: {now_s}")
        if not self.plotted_before:
            ax.set_xlabel("time", fontsize=FONTSIZE)
            ax.set_ylabel("% correct", fontsize=FONTSIZE)
            _ylabel_on_right(ax)
            ax.margins(0.01, 0.01)

    @enforce_types
    def _plot_pdr_profit_vs_ptrue(self):
        ax = self.ax_pdr_profit_vs_ptrue
        stake_amt = self.ppss.predictoor_ss.stake_amount.amt_eth
        mnp, mxp = -stake_amt, stake_amt
        avg = np.average(self.st.pdr_profits_OCEAN)
        next_profits = _slice(self.st.pdr_profits_OCEAN, self.N_done, self.N)
        next_probs_up = _slice(self.st.probs_up, self.N_done, self.N)

        c = (random(), random(), random())  # random RGB color
        ax.scatter(next_probs_up, next_profits, color=c, s=1)

        s = f"pdr profit dist. avg={avg:.2f} OCEAN"
        _set_title(ax, s)
        ax.plot([0.5, 0.5], [mnp, mxp], c="0.2", ls="-", lw=1)
        if not self.plotted_before:
            ax.plot([0.0, 1.0], [0, 0], c="0.2", ls="--", lw=1)
            _set_xlabel(ax, "prob(up)")
            _set_ylabel(ax, "pdr profit (OCEAN)")
            _ylabel_on_right(ax)
            ax.margins(0.05, 0.05)

    @enforce_types
    def _plot_trader_profit_vs_ptrue(self):
        ax = self.ax_trader_profit_vs_ptrue
        mnp = min(self.st.trader_profits_USD)
        mxp = max(self.st.trader_profits_USD)
        avg = np.average(self.st.trader_profits_USD)
        next_profits = _slice(self.st.trader_profits_USD, self.N_done, self.N)
        next_probs_up = _slice(self.st.probs_up, self.N_done, self.N)

        c = (random(), random(), random())  # random RGB color
        ax.scatter(next_probs_up, next_profits, color=c, s=1)

        s = f"trader profit dist. avg={avg:.2f} USD"

        _set_title(ax, s)
        ax.plot([0.5, 0.5], [mnp, mxp], c="0.2", ls="-", lw=1)
        if not self.plotted_before:
            ax.plot([0.0, 1.0], [0, 0], c="0.2", ls="--", lw=1)
            _set_xlabel(ax, "prob(up)")
            _set_ylabel(ax, "trader profit (USD)")
            _ylabel_on_right(ax)
            ax.margins(0.05, 0.05)

    @enforce_types
    def _plot_aimodel_varimps(self, d: AimodelPlotdata):
        ax = self.ax_aimodel_varimps
        imps_tups = d.model.importance_per_var(include_stddev=True)
        plot_aimodel_varimps(d.colnames, imps_tups, (self.fig, ax))
        if not self.plotted_before:
            ax.margins(0.01, 0.01)

    @enforce_types
    def _plot_aimodel_response(self, d: AimodelPlotdata):
        ax = self.ax_aimodel_response
        plot_aimodel_response(d, (self.fig, ax))
        if not self.plotted_before:
            ax.margins(0.01, 0.01)


@enforce_types
def _slice(a: list, N_done: int, N: int) -> list:
    return [a[i] for i in range(max(0, N_done - 1), N)]


@enforce_types
def _set_xlabel(ax, s: str):
    ax.set_xlabel(s, fontsize=FONTSIZE)


@enforce_types
def _set_ylabel(ax, s: str):
    ax.set_ylabel(s, fontsize=FONTSIZE)


@enforce_types
def _set_title(ax, s: str):
    ax.set_title(s, fontsize=FONTSIZE, fontweight="bold")


@enforce_types
def _ylabel_on_right(ax):
    ax.yaxis.tick_right()
    ax.yaxis.set_label_position("right")


@enforce_types
def _del_lines(ax):
    for l in ax.lines:
        l.remove()
