#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import glob
import os
import pickle
import time
from datetime import datetime
from pathlib import Path

from enforce_typing import enforce_types
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from pdr_backend.sim.constants import Dirn, dirn_str, UP, DOWN

HEIGHT = 7.5
WIDTH = int(HEIGHT * 3.2)


# pylint: disable=too-many-instance-attributes,attribute-defined-outside-init
class SimPlotter:
    @enforce_types
    def __init__(
        self,
    ):
        self.st = None
        self.aimodel_plotdata = None
        self.multi_id = None

    @staticmethod
    @enforce_types
    def get_latest_run_id():
        if not os.path.exists("sim_state"):
            raise Exception(
                "sim_state folder does not exist. Please run the simulation first."
            )
        path = sorted(Path("sim_state").iterdir(), key=os.path.getmtime)[-1]
        return str(path).replace("sim_state/", "")

    @staticmethod
    @enforce_types
    def get_all_run_names():
        path = Path("sim_state").iterdir()
        return [str(p).replace("sim_state/", "") for p in path]

    @enforce_types
    def load_state(self, multi_id):
        root_path = f"sim_state/{multi_id}"

        if not os.path.exists("sim_state"):
            raise Exception(
                "sim_state folder does not exist. Please run the simulation first."
            )

        if not os.path.exists(root_path):
            raise Exception(
                f"sim_state/{multi_id} folder does not exist. Please run the simulation first."
            )

        all_state_files = glob.glob(f"{root_path}/st_*.pkl")
        if not all_state_files:
            raise Exception("No state files found. Please run the simulation first.")

        if not os.path.exists(f"{root_path}/st_final.pkl"):
            latest_st_file, latest_aimodel_file = _get_latest_usable_state(root_path)
            with open(latest_st_file, "rb") as f:
                self.st = pickle.load(f)

            with open(latest_aimodel_file, "rb") as f:
                self.aimodel_plotdata = pickle.load(f)

            return self.st, latest_st_file.replace(f"{root_path}/st_", "").replace(
                ".pkl", ""
            )

        # make sure the final state is written to disk before unpickling
        # avoid race conditions with the pickling itself
        if file_age_in_seconds(f"{root_path}/st_final.pkl") < 3:
            time.sleep(3)

        with open(f"{root_path}/st_final.pkl", "rb") as f:
            self.st = pickle.load(f)

        with open(f"{root_path}/aimodel_plotdata_final.pkl", "rb") as f:
            self.aimodel_plotdata = pickle.load(f)

        return self.st, "final"

    @enforce_types
    def init_state(self, multi_id):
        files = glob.glob("sim_state/{multi_id}/*")

        self.multi_id = multi_id

        for f in files:
            os.remove(f)

        os.makedirs(f"sim_state/{multi_id}")

    @enforce_types
    def save_state(self, sim_state, aimodel_plotdata, is_final: bool = False):
        root_path = f"sim_state/{self.multi_id}"
        ts = (
            datetime.now().strftime("%Y%m%d_%H%M%S.%f")[:-3]
            if not is_final
            else "final"
        )

        existing_states = sorted(
            glob.glob(f"{root_path}/st_*.pkl"), key=os.path.getmtime
        )
        existing_aimodel_plotdata = sorted(
            glob.glob(f"{root_path}/aimodel_plotdata_*.pkl"), key=os.path.getmtime
        )

        if existing_states and not is_final:
            # remove old files, but if state is not final,
            # keep next to last so that the runner knows the sim
            # is running and not warming up
            existing_states = existing_states[:-1]
            existing_aimodel_plotdata = existing_aimodel_plotdata[:-1]

        for fl in existing_states:
            os.remove(fl)

        for fl in existing_aimodel_plotdata:
            os.remove(fl)

        with open(f"{root_path}/st_{ts}.pkl", "wb") as f:
            pickle.dump(sim_state, f)

        with open(f"{root_path}/aimodel_plotdata_{ts}.pkl", "wb") as f:
            pickle.dump(aimodel_plotdata, f)

    @enforce_types
    def plot_pdr_profit_vs_time(self):
        profits = self.st.hist_profits.pdr_profits_OCEAN
        cum_profits = list(np.cumsum(profits))
        ylabel = "predictoor profit (OCEAN)"
        title = f"Pdr profit vs time. Current: {cum_profits[-1]:.2f} OCEAN"
        title += f". Avg profit per iter: {np.average(profits):.4f} OCEAN"
        fig = make_subplots(rows=1, cols=1, subplot_titles=(title,))
        self._add_subplot_y_vs_time(fig, cum_profits, ylabel, "lines", row=1, col=1)
        return fig

    @enforce_types
    def plot_trader_profit_vs_time(self):
        profits = self.st.hist_profits.trader_profits_USD
        cum_profits = list(np.cumsum(profits))
        ylabel = "trader profit (USD)"
        title = f"Trader profit vs time. Current: ${cum_profits[-1]:.2f}"
        title += f". Avg profit per iter: ${np.average(profits):.4f}"
        fig = make_subplots(rows=1, cols=1, subplot_titles=(title,))
        self._add_subplot_y_vs_time(fig, cum_profits, ylabel, "lines", row=1, col=1)
        return fig

    @enforce_types
    def _add_subplot_y_vs_time(self, fig, y, ylabel, mode, row, col):
        assert mode in ["markers", "lines"], mode
        line, marker = None, None
        if mode == "markers":
            marker = {"color": "black", "size": 2}
        elif mode == "lines":
            line = {"color": "#636EFA"}

        x = list(range(len(y)))

        fig.add_traces(
            [
                # points: y vs time
                go.Scatter(
                    x=x,
                    y=y,
                    mode=mode,
                    marker=marker,
                    line=line,
                    showlegend=False,
                ),
                # line: horizontal error = 0
                go.Scatter(
                    x=[min(x), max(x)],
                    y=[0.0, 0.0],
                    mode="lines",
                    line={"color": "grey", "dash": "dot"},
                    showlegend=False,
                ),
            ],
            rows=[row] * 2,
            cols=[col] * 2,
        )
        fig.update_xaxes(title="time", row=row, col=col)
        fig.update_yaxes(title=ylabel, row=row, col=col)

        return fig

    @enforce_types
    def plot_pdr_profit_vs_ptrue(self):
        return self._plot_profit_vs_ptrue(is_pdr=True)

    @enforce_types
    def plot_trader_profit_vs_ptrue(self):
        return self._plot_profit_vs_ptrue(is_pdr=False)

    @enforce_types
    def _plot_profit_vs_ptrue(self, is_pdr: bool):
        titles = [self._profit_dist_title(is_pdr, dirn) for dirn in [UP, DOWN]]

        # make subplots
        fig = make_subplots(rows=1, cols=2, subplot_titles=titles)

        # fill in subplots
        self._add_subplot_profit_dist(fig, is_pdr, UP, row=1, col=1)
        self._add_subplot_profit_dist(fig, is_pdr, DOWN, row=1, col=2)

        # global: set ticks
        minor = {"ticks": "inside", "showgrid": True}
        rng = [0.5, 1.0]
        for col in [1, 2]:
            fig.update_xaxes(minor=minor, range=rng, dtick=0.1, row=1, col=col)
            fig.update_yaxes(minor=minor, row=1, col=col)

        # global: don't show legend
        fig.update_layout(showlegend=False)

        return fig

    @enforce_types
    def _profit_dist_title(self, is_pdr: bool, dirn: Dirn) -> str:
        if is_pdr:
            return f"Pdr profit dist'n vs prob({dirn_str(dirn)})"

        return f"Trader profit dist'n vs prob({dirn_str(dirn)})"

    @enforce_types
    def _add_subplot_profit_dist(
        self,
        fig,
        is_pdr: bool,
        dirn: Dirn,
        row: int,
        col: int,
    ):
        dirn_s = dirn_str(dirn)
        x = np.array(self.st.true_vs_pred[dirn].predprobs)
        if is_pdr:
            y = np.array(self.st.hist_profits.pdr_profits_OCEAN)
        else:
            y = np.array(self.st.hist_profits.trader_profits_USD)
        I = (x >= 0.5).nonzero()[0]
        if len(I) > 0:
            x, y = x[I], y[I]
        fig.add_traces(
            [
                # line: profit vs ptrue scatterplot
                go.Scatter(
                    x=x,
                    y=y,
                    mode="markers",
                    marker={"color": "#636EFA", "size": 2},
                ),
                # line: 0.0 horizontal
                go.Scatter(
                    x=[min(x), max(x)],
                    y=[0.0, 0.0],
                    mode="lines",
                    name="",
                    line_dash="dot",
                ),
            ],
            rows=[row] * 2,
            cols=[col] * 2,
        )

        fig.update_xaxes(title=f"prob({dirn_s})", row=row, col=col)

        if is_pdr:
            ytitle = "pdr profit (OCEAN)"
        else:
            ytitle = "trader profit (USD)"
        fig.update_yaxes(title=ytitle, row=row, col=col)

    @enforce_types
    def plot_model_performance_vs_time(self):
        # set titles
        titles = [
            self._acc_title(UP),
            self._acc_title(DOWN),
            self._f1_title(UP),
            self._f1_title(DOWN),
            self._loss_title(UP),
            self._loss_title(DOWN),
        ]

        # make subplots
        fig = make_subplots(
            rows=3,
            cols=2,
            subplot_titles=titles,
            vertical_spacing=0.08,
        )

        # fill in subplots
        self._add_subplot_accuracy_vs_time(fig, UP, row=1, col=1)
        self._add_subplot_accuracy_vs_time(fig, DOWN, row=1, col=2)
        self._add_subplot_f1_precision_recall_vs_time(fig, UP, row=2, col=1)
        self._add_subplot_f1_precision_recall_vs_time(fig, DOWN, row=2, col=2)
        self._add_subplot_log_loss_vs_time(fig, UP, row=3, col=1)
        self._add_subplot_log_loss_vs_time(fig, DOWN, row=3, col=2)

        # global: set minor ticks
        minor = {"ticks": "inside", "showgrid": True}
        for row in [1, 2, 3]:
            fig.update_yaxes(minor=minor, row=row, col=1)
            fig.update_xaxes(minor=minor, row=row, col=1)

        # global: share x-axes of subplots
        fig.update_layout(
            {
                "xaxis": {"matches": "x", "showticklabels": True},
                "xaxis3": {"matches": "x", "showticklabels": True},
                "xaxis5": {"matches": "x", "showticklabels": True},
                "xaxis2": {"matches": "x2", "showticklabels": True},
                "xaxis4": {"matches": "x2", "showticklabels": True},
                "xaxis6": {"matches": "x2", "showticklabels": True},
            }
        )
        fig.update_xaxes(title="time", row=3, col=1)
        fig.update_xaxes(title="time", row=3, col=2)

        # global: don't show legend
        fig.update_layout(showlegend=False)

        return fig

    @enforce_types
    def _acc_title(self, dirn: Dirn) -> str:
        hist_perfs, dirn_s = self.st.hist_perfs[dirn], dirn_str(dirn)
        s = f"{dirn_s} accuracy={hist_perfs.acc_ests[-1]*100:.1f}% "
        s += f"[{hist_perfs.acc_ls[-1]*100:.1f}%, {hist_perfs.acc_us[-1]*100:.1f}%]"
        return s

    @enforce_types
    def _f1_title(self, dirn: Dirn) -> str:
        hist_perfs, dirn_s = self.st.hist_perfs[dirn], dirn_str(dirn)
        s = f"{dirn_s} f1={hist_perfs.f1s[-1]:.2f}"
        s += f" [recall={hist_perfs.recalls[-1]:.2f}"
        s += f", prec'n={hist_perfs.precisions[-1]:.2f}]"
        return s

    @enforce_types
    def _loss_title(self, dirn: Dirn) -> str:
        hist_perfs, dirn_s = self.st.hist_perfs[dirn], dirn_str(dirn)
        s = f"{dirn_s} log loss = {hist_perfs.losses[-1]:.2f}"
        return s

    @enforce_types
    def _add_subplot_accuracy_vs_time(self, fig, dirn: Dirn, row: int, col: int):
        hist_perfs = self.st.hist_perfs[dirn]
        acc_ests = [100 * a for a in hist_perfs.acc_ests]
        df = pd.DataFrame(acc_ests, columns=["accuracy"])
        df["acc_ls"] = [100 * a for a in hist_perfs.acc_ls]
        df["acc_us"] = [100 * a for a in hist_perfs.acc_us]
        df["time"] = range(len(hist_perfs.acc_ests))

        fig.add_traces(
            [
                # line: lower bound
                go.Scatter(
                    x=df["time"],
                    y=df["acc_us"],
                    mode="lines",
                    fill=None,
                    name="accuracy upper bound",
                    marker_color="#636EFA",
                ),
                # line: upper bound
                go.Scatter(
                    x=df["time"],
                    y=df["acc_ls"],
                    mode="lines",
                    fill="tonexty",
                    name="accuracy lower bound",
                    marker_color="#636EFA",
                ),
                # line: estimated accuracy
                go.Scatter(
                    x=df["time"],
                    y=df["accuracy"],
                    mode="lines",
                    name="accuracy",
                    marker_color="#000000",
                ),
                # line: 50% horizontal
                go.Scatter(
                    x=[min(df["time"]), max(df["time"])],
                    y=[50, 50],
                    mode="lines",
                    marker_color="grey",
                ),
            ],
            rows=[row] * 4,
            cols=[col] * 4,
        )
        fig.update_yaxes(title_text="accuracy (%)", row=1, col=1)

    @enforce_types
    def _add_subplot_f1_precision_recall_vs_time(self, fig, dirn, row, col):
        hist_perfs = self.st.hist_perfs[dirn]
        df = pd.DataFrame(hist_perfs.f1s, columns=["f1"])
        df["precisions"] = hist_perfs.precisions
        df["recalls"] = hist_perfs.recalls
        df["time"] = range(len(hist_perfs.f1s))

        fig.add_traces(
            [
                # line: f1
                go.Scatter(
                    x=df["time"],
                    y=df["f1"],
                    mode="lines",
                    name="f1",
                    marker_color="#72B7B2",
                ),
                # line: precision
                go.Scatter(
                    x=df["time"],
                    y=df["precisions"],
                    mode="lines",
                    name="precision",
                    marker_color="#AB63FA",
                ),
                # line: recall
                go.Scatter(
                    x=df["time"],
                    y=df["recalls"],
                    mode="lines",
                    name="recall",
                    marker_color="#636EFA",
                ),
                # line: 0.5 horizontal
                go.Scatter(
                    x=[min(df["time"]), max(df["time"])],
                    y=[0.5, 0.5],
                    mode="lines",
                    name="",
                    marker_color="grey",
                ),
            ],
            rows=[row] * 4,
            cols=[col] * 4,
        )
        fig.update_yaxes(title_text="f1, etc", row=2, col=1)

    @enforce_types
    def _add_subplot_log_loss_vs_time(self, fig, dirn: Dirn, row: int, col: int):
        hist_perfs = self.st.hist_perfs[dirn]
        df = pd.DataFrame(hist_perfs.losses, columns=["log loss"])
        df["time"] = range(len(hist_perfs.losses))

        fig.add_trace(
            go.Scatter(
                x=df["time"],
                y=df["log loss"],
                mode="lines",
                name="",
                marker_color="#636EFA",
            ),
            row=row,
            col=col,
        )
        fig.update_yaxes(title_text="log loss", row=3, col=1)


@enforce_types
def file_age_in_seconds(pathname):
    stat_result = os.stat(pathname)
    return time.time() - stat_result.st_mtime


@enforce_types
def _get_latest_usable_state(root_path: str):
    all_state_files = glob.glob(f"{root_path}/st_*.pkl")
    all_state_files.sort()
    latest_file = all_state_files[-1]

    aimodel_filename = latest_file.replace("st_", "aimodel_plotdata_")

    if os.path.exists(aimodel_filename):
        return latest_file, aimodel_filename

    # if the process was interrupted on aimodel filename creation,
    # the pair is invalid ==> use next to last state if exists

    if len(all_state_files) < 1:
        raise Exception("No valid state files found. Please run the simulation first.")

    latest_file = all_state_files[-2]
    aimodel_filename = latest_file.replace("st_", "aimodel_plotdata_")

    if not os.path.exists(aimodel_filename):
        raise Exception(
            "No valid aimodel_plotdata file found. Please run the simulation again."
        )

    return latest_file, aimodel_filename
