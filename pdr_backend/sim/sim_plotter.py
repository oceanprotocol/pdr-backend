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

from pdr_backend.aimodel.aimodel_plotdata import AimodelPlotdata

from pdr_backend.statutil.autocorrelation_plotdata import (
    AutocorrelationPlotdataFactory,
)
from pdr_backend.statutil.autocorrelation_plotter import add_corr_traces
from pdr_backend.statutil.dist_plotdata import DistPlotdataFactory
from pdr_backend.statutil.dist_plotter import add_pdf, add_cdf, add_nq

HEIGHT = 7.5
WIDTH = int(HEIGHT * 3.2)


# pylint: disable=too-many-instance-attributes
class SimPlotter:
    @enforce_types
    def __init__(
        self,
    ):
        self.st = None
        self.aimodel_plotdata = None
        self.multi_id = None

    @staticmethod
    def get_latest_run_id():
        if not os.path.exists("sim_state"):
            raise Exception(
                "sim_state folder does not exist. Please run the simulation first."
            )
        path = sorted(Path("sim_state").iterdir(), key=os.path.getmtime)[-1]
        return str(path).replace("sim_state/", "")

    @staticmethod
    def get_all_run_names():
        path = Path("sim_state").iterdir()
        return [str(p).replace("sim_state/", "") for p in path]

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

    def init_state(self, multi_id):
        files = glob.glob("sim_state/{multi_id}/*")

        self.multi_id = multi_id

        for f in files:
            os.remove(f)

        os.makedirs(f"sim_state/{multi_id}")

    def save_state(
        self, sim_state, aimodel_plotdata: AimodelPlotdata, is_final: bool = False
    ):
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
        y = list(np.cumsum(self.st.pdr_profits_OCEAN))
        ylabel = "predictoor profit (OCEAN)"
        title = f"Predictoor profit vs time. Current: {y[-1]:.2f} OCEAN"
        fig = make_subplots(rows=1, cols=1, subplot_titles=(title,))
        self._add_subplot_y_vs_time(fig, y, ylabel, "lines", row=1, col=1)
        return fig

    @enforce_types
    def plot_trader_profit_vs_time(self):
        y = list(np.cumsum(self.st.trader_profits_USD))
        ylabel = "trader profit (USD)"
        title = f"Trader profit vs time. Current: ${y[-1]:.2f}"
        fig = make_subplots(rows=1, cols=1, subplot_titles=(title,))
        self._add_subplot_y_vs_time(fig, y, ylabel, "lines", row=1, col=1)
        return fig

    @enforce_types
    def plot_pdr_profit_vs_ptrue(self):
        x = self.st.probs_up
        y = self.st.pdr_profits_OCEAN
        fig = go.Figure(
            go.Scatter(
                x=x,
                y=y,
                mode="markers",
                marker={"color": "#636EFA", "size": 2},
            )
        )
        fig.add_hline(y=0, line_dash="dot", line_color="grey")
        title = f"Predictoor profit dist. avg={np.average(y):.2f} OCEAN"
        fig.update_layout(title=title)
        fig.update_xaxes(title="prob(up)")
        fig.update_yaxes(title="pdr profit (OCEAN)")

        return fig

    @enforce_types
    def plot_trader_profit_vs_ptrue(self):
        x = self.st.probs_up
        y = self.st.trader_profits_USD
        fig = go.Figure(
            go.Scatter(
                x=x,
                y=y,
                mode="markers",
                marker={"color": "#636EFA", "size": 2},
            )
        )
        fig.add_hline(y=0, line_dash="dot", line_color="grey")
        title = f"trader profit dist. avg={np.average(y):.2f} USD"
        fig.update_layout(title=title)
        fig.update_xaxes(title="prob(up)")
        fig.update_yaxes(title="trader profit (USD)")

        return fig

    @enforce_types
    def plot_model_performance_vs_time(self):
        # set titles
        aim = self.st.aim
        s1 = f"accuracy = {aim.acc_ests[-1]*100:.2f}% "
        s1 += f"[{aim.acc_ls[-1]*100:.2f}%, {aim.acc_us[-1]*100:.2f}%]"

        s2 = f"f1={aim.f1s[-1]:.4f}"
        s2 += f" [recall={aim.recalls[-1]:.4f}"
        s2 += f", precision={aim.precisions[-1]:.4f}]"

        s3 = f"log loss = {aim.losses[-1]:.4f}"

        # make subplots
        fig = make_subplots(
            rows=3,
            cols=1,
            subplot_titles=(s1, s2, s3),
            vertical_spacing=0.08,
        )

        # fill in subplots
        self._add_subplot_accuracy_vs_time(fig, row=1)
        self._add_subplot_f1_precision_recall_vs_time(fig, row=2)
        self._add_subplot_log_loss_vs_time(fig, row=3)

        # global: set minor ticks
        minor = {"ticks": "inside", "showgrid": True}
        for row in [1, 2, 3]:
            fig.update_yaxes(minor=minor, row=row, col=1)
            fig.update_xaxes(minor=minor, row=row, col=1)

        # global: share x-axes of subplots
        fig.update_layout(
            {
                "xaxis": {"matches": "x", "showticklabels": True},
                "xaxis2": {"matches": "x", "showticklabels": True},
                "xaxis3": {"matches": "x", "showticklabels": True},
            }
        )
        fig.update_xaxes(title="time", row=3, col=1)

        # global: don't show legend
        fig.update_layout(showlegend=False)

        return fig

    @enforce_types
    def _add_subplot_accuracy_vs_time(self, fig, row):
        aim = self.st.aim
        acc_ests = [100 * a for a in aim.acc_ests]
        df = pd.DataFrame(acc_ests, columns=["accuracy"])
        df["acc_ls"] = [100 * a for a in aim.acc_ls]
        df["acc_us"] = [100 * a for a in aim.acc_us]
        df["time"] = range(len(aim.acc_ests))

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
            cols=[1] * 4,
        )
        fig.update_yaxes(title_text="accuracy (%)", row=1, col=1)

    @enforce_types
    def _add_subplot_f1_precision_recall_vs_time(self, fig, row):
        aim = self.st.aim
        df = pd.DataFrame(aim.f1s, columns=["f1"])
        df["precisions"] = aim.precisions
        df["recalls"] = aim.recalls
        df["time"] = range(len(aim.f1s))

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
            cols=[1] * 4,
        )
        fig.update_yaxes(title_text="f1, etc", row=2, col=1)

    @enforce_types
    def _add_subplot_log_loss_vs_time(self, fig, row):
        aim = self.st.aim
        df = pd.DataFrame(aim.losses, columns=["log loss"])
        df["time"] = range(len(aim.losses))

        fig.add_trace(
            go.Scatter(x=df["time"], y=df["log loss"], mode="lines", name="log loss"),
            row=row,
            col=1,
        )
        fig.update_yaxes(title_text="log loss", row=3, col=1)

    @enforce_types
    def plot_prediction_residuals_dist(self):
        if _model_is_classif(self.st):
            return empty_fig("(Nothing to show because model is a classifier.)")

        # calc data
        d = DistPlotdataFactory.build(self.st.aim.yerrs)

        # initialize subplots
        s1, s2, s3 = "Residuals distribution", "", ""
        fig = make_subplots(
            rows=3,
            cols=1,
            subplot_titles=(s1, s2, s3),
            vertical_spacing=0.02,
            shared_xaxes=True,
        )

        # fill in subplots
        add_pdf(fig, d, row=1, col=1)
        add_cdf(fig, d, row=2, col=1)
        add_nq(fig, d, row=3, col=1)

        # global: set minor ticks
        minor = {"ticks": "inside", "showgrid": True}
        fig.update_yaxes(minor=minor, row=1, col=1)
        for row in [2, 3, 4, 5]:
            fig.update_yaxes(minor=minor, row=row, col=1)
            fig.update_xaxes(minor=minor, row=row, col=1)

        return fig

    @enforce_types
    def plot_prediction_residuals_other(self):
        if _model_is_classif(self.st):
            return empty_fig()

        # calc data
        nlags = 10  # magic number alert # FIX ME: have spinner, like ARIMA feeds
        d = AutocorrelationPlotdataFactory.build(self.st.aim.yerrs, nlags=nlags)

        # initialize subplots
        s1 = "Residuals vs time"
        s2 = "Residuals correlogram"
        fig = make_subplots(
            rows=2,
            cols=1,
            subplot_titles=(s1, s2),
            vertical_spacing=0.12,
        )

        # fill in subplots
        self._add_subplot_residual_vs_time(fig, row=1, col=1)
        add_corr_traces(
            fig,
            d.acf_results,
            row=2,
            col=1,
            ylabel="autocorrelation (ACF)",
        )

        return fig

    @enforce_types
    def _add_subplot_residual_vs_time(self, fig, row, col):
        y = self.st.aim.yerrs
        self._add_subplot_y_vs_time(fig, y, "residual", "markers", row, col)

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
def file_age_in_seconds(pathname):
    stat_result = os.stat(pathname)
    return time.time() - stat_result.st_mtime


@enforce_types
def _model_is_classif(sim_state) -> bool:
    yerrs = sim_state.aim.yerrs
    return min(yerrs) == max(yerrs) == 0.0


@enforce_types
def empty_fig(title=""):
    fig = go.Figure()
    w = "white"
    fig.update_layout(title=title, paper_bgcolor=w, plot_bgcolor=w)
    fig.update_xaxes(visible=False, showgrid=False, gridcolor=w, zerolinecolor=w)
    fig.update_yaxes(visible=False, showgrid=False, gridcolor=w, zerolinecolor=w)
    return fig


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
