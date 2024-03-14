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

import streamlit as streamlit
streamlit.set_page_config(layout="wide")


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

        plt.close("all")

        # so labels are above lines. Must be before figure()
        plt.rcParams["axes.axisbelow"] = False

        c1, c2, c3 = streamlit.columns((1, 2, 1))
        c11, c12 = c1.container(), c1.container()
        c31, c32 = c3.container(), c3.container()

        c4, c5 = streamlit.columns((1, 1))

        self.canvas = {
            "pdr_profit_vs_time": c11.empty(),
            "trader_profit_vs_time": c12.empty(),
            "accuracy_vs_time": c2.empty(),
            "pdr_profit_vs_ptrue": c31.empty(),
            "trader_profit_vs_ptrue": c32.empty(),
            "aimodel_varimps": c4.empty(),
            "aimodel_response": c5.empty(),
        }

        self.figs = {}

        for k in self.canvas.keys():
            fig, ax = plt.subplots()
            self.figs[k] = fig
            setattr(self, f"ax_{k}", ax)

        # attributes to help update plots' state quickly
        self.N: int = 0
        self.N_done: int = 0
        self.x: List[float] = []

        self.y01_est: List[float] = []
        self.y01_l: List[float] = []
        self.y01_u: List[float] = []
        self.plotted_before: bool = False

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
        #plt.subplots_adjust(wspace=0.3)
        plt.pause(0.001)
        self.plotted_before = True

        plt.ion()
        plt.show()

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

        self.canvas["pdr_profit_vs_time"].pyplot(self.figs["pdr_profit_vs_time"])

        if not self.plotted_before:
            ax.set_ylabel("predictoor profit (OCEAN)", fontsize=FONTSIZE)
            ax.set_xlabel("time", fontsize=FONTSIZE)
            _ylabel_on_right(ax)

    @enforce_types
    def _plot_trader_profit_vs_time(self):
        ax = self.ax_trader_profit_vs_time
        y10 = list(np.cumsum(self.st.trader_profits_USD))
        next_y10 = _slice(y10, self.N_done, self.N)
        ax.plot(self.next_x, next_y10, c="b")
        ax.plot(self.next_hx, [0, 0], c="0.2", ls="--", lw=1)
        _set_title(ax, f"Trader profit vs time. Current: ${y10[-1]:.2f}")

        self.canvas["trader_profit_vs_time"].pyplot(self.figs["trader_profit_vs_time"])
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

        self.canvas["accuracy_vs_time"].pyplot(self.figs["accuracy_vs_time"])
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

        self.canvas["pdr_profit_vs_ptrue"].pyplot(self.figs["pdr_profit_vs_ptrue"])
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

        self.canvas["trader_profit_vs_ptrue"].pyplot(self.figs["trader_profit_vs_ptrue"])
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
        plot_aimodel_varimps(d.colnames, imps_tups, (self.figs["aimodel_varimps"], ax))

        self.canvas["aimodel_varimps"].pyplot(self.figs["aimodel_varimps"])
        if not self.plotted_before:
            ax.margins(0.01, 0.01)

    @enforce_types
    def _plot_aimodel_response(self, d: AimodelPlotdata):
        ax = self.ax_aimodel_response
        plot_aimodel_response(d, (self.figs["aimodel_varimps"], ax))

        self.canvas["aimodel_response"].pyplot(self.figs["aimodel_response"])
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
