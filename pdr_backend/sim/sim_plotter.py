from typing import List

from enforce_typing import enforce_types
from matplotlib import gridspec
import matplotlib.pyplot as plt
from matplotlib.pyplot import savefig
import numpy as np
from numpy.random import random

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

        gs = gridspec.GridSpec(2, 6, width_ratios=[5, 1, 2, 0.6, 2, 3])

        self.ax_pdr_profit_vs_time = fig.add_subplot(gs[0, 0])
        self.ax_trader_profit_vs_time = fig.add_subplot(gs[1, 0])

        self.ax_pdr_profit_vs_ptrue = fig.add_subplot(gs[0, 1])
        self.ax_trader_profit_vs_ptrue = fig.add_subplot(gs[1, 1])

        self.ax_accuracy_vs_time = fig.add_subplot(gs[0, 2])
        self.ax_f1_precision_recall_vs_time = fig.add_subplot(gs[1, 2])

        # col 3 is empty, for overflow of aimodel_varimps's y-axis labels
        self.ax_aimodel_varimps = fig.add_subplot(gs[:, 4])

        self.ax_aimodel_response = fig.add_subplot(gs[:, 5])

        # attributes to help update plots' state quickly
        self.N: int = 0
        self.N_done: int = 0
        self.x: List[float] = []

        self.shown_plot_before: bool = False
        self.computed_plot_before: bool = False

    # pylint: disable=too-many-statements
    @enforce_types
    def compute_plot(
            self,
            aimodel_plotdata: AimodelPlotdata,
            do_show_plot: bool,
            do_save_plot: bool,
    ) -> Optional[str]:
        """
        @description
          Create / update whole plot, with many subplots

        @arguments
          aimodel_plotdata -- has model, X_train, etc
          do_show_plot -- render on-screen in a window?
          do_save_plot -- export as png?

        @return
          plot_filename - filename of saved plot (None if not done)
        """
        if do_show_plot and not self.shown_plot_before:
            # push plot to screen
            plt.ion()
            plt.show()
            self.shown_plot_before = True

        # update N, N_done, x. **Update x only after updating N, N_done!**
        self.N = len(self.st.pdr_profits_OCEAN)
        self.N_done = len(self.x)  # what # points have been plotted previously
        self.x = list(range(0, self.N))

        # main work: create/update subplots
        self._plot_pdr_profit_vs_time()
        self._plot_trader_profit_vs_time()

        self._plot_accuracy_vs_time()
        self._plot_f1_precision_recall_vs_time()
        self._plot_pdr_profit_vs_ptrue()
        self._plot_trader_profit_vs_ptrue()

        self._plot_aimodel_varimps(aimodel_plotdata)
        self._plot_aimodel_response(aimodel_plotdata)

        # final pieces of making plot
        self.fig.set_size_inches(WIDTH, HEIGHT)
        self.fig.tight_layout(pad=0.5, h_pad=1.0, w_pad=1.0)
        plt.subplots_adjust(wspace=0.3)

        # save to png?
        plot_filename = None
        if do_save_plot:
            plot_filename = ppss.sim_ss.unique_final_img_filename()
            savefig(filename)

        # wrapup for reloop
        if do_show_plot:
            plt.pause(0.001)
        self.computed_plot_before = True

        return plot_filename
            

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
        if not self.computed_plot_before:
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
        if not self.computed_plot_before:
            ax.set_xlabel("time", fontsize=FONTSIZE)
            ax.set_ylabel("trader profit (USD)", fontsize=FONTSIZE)
            _ylabel_on_right(ax)
            ax.margins(0.005, 0.05)

    @enforce_types
    def _plot_accuracy_vs_time(self):
        ax = self.ax_accuracy_vs_time
        clm = self.st.clm
        next_acc_ests = _slice(clm.acc_ests, self.N_done, self.N, mult=100.0)
        next_acc_ls = _slice(clm.acc_ls, self.N_done, self.N, mult=100.0)
        next_acc_us = _slice(clm.acc_us, self.N_done, self.N, mult=100.0)

        ax.plot(self.next_x, next_acc_ests, "green")
        ax.fill_between(self.next_x, next_acc_ls, next_acc_us, color="0.9")
        ax.plot(self.next_hx, [0.5 * 100.0, 0.5 * 100.0], c="0.2", ls="--", lw=1)
        ax.set_ylim(bottom=0.4 * 100.0, top=0.6 * 100.0)
        s = f"accuracy = {clm.acc_ests[-1]*100:.2f}% "
        s += f"[{clm.acc_ls[-1]*100:.2f}%, {clm.acc_us[-1]*100:.2f}%]"
        _set_title(ax, s)
        if not self.computed_plot_before:
            ax.set_xlabel("time", fontsize=FONTSIZE)
            ax.set_ylabel("% correct [lower, upper bound]", fontsize=FONTSIZE)
            _ylabel_on_right(ax)
            ax.margins(0.01, 0.01)

    @enforce_types
    def _plot_f1_precision_recall_vs_time(self):
        ax = self.ax_f1_precision_recall_vs_time
        clm = self.st.clm
        next_f1s = _slice(clm.f1s, self.N_done, self.N)
        next_precisions = _slice(clm.precisions, self.N_done, self.N)
        next_recalls = _slice(clm.recalls, self.N_done, self.N)

        ax.plot(self.next_x, next_precisions, "darkred", label="precision")  # top
        ax.plot(self.next_x, next_f1s, "indianred", label="f1")  # mid
        ax.plot(self.next_x, next_recalls, "lightcoral", label="recall")  # bot
        ax.fill_between(self.next_x, next_recalls, next_precisions, color="0.9")
        ax.plot(self.next_hx, [0.5, 0.5], c="0.2", ls="--", lw=1)
        ax.set_ylim(bottom=0.25, top=0.75)
        s = f"f1={clm.f1s[-1]:.4f}"
        s += f" [recall={clm.recalls[-1]:.4f}"
        s += f", precision={clm.precisions[-1]:.4f}]"
        _set_title(ax, s)
        if not self.computed_plot_before:
            ax.set_xlabel("time", fontsize=FONTSIZE)
            ax.set_ylabel("f1 [recall, precision]", fontsize=FONTSIZE)
            ax.legend(loc="lower left")
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
        if not self.computed_plot_before:
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
        if not self.computed_plot_before:
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
        if not self.computed_plot_before:
            ax.margins(0.01, 0.01)

    @enforce_types
    def _plot_aimodel_response(self, d: AimodelPlotdata):
        ax = self.ax_aimodel_response
        plot_aimodel_response(d, (self.fig, ax))
        if not self.computed_plot_before:
            ax.margins(0.01, 0.01)


@enforce_types
def _slice(a: list, N_done: int, N: int, mult: float = 1.0) -> list:
    return [a[i] * mult for i in range(max(0, N_done - 1), N)]


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
