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
            # plot previous state to avoid using a pickle that hasn't finished
            all_state_files = glob.glob(f"{root_path}/st_*.pkl")
            all_state_files.sort()
            latest_file = all_state_files[-1]
            with open(latest_file, "rb") as f:
                self.st = pickle.load(f)

            with open(latest_file.replace("st_", "aimodel_plotdata_"), "rb") as f:
                self.aimodel_plotdata = pickle.load(f)

            return self.st, latest_file.replace(f"{root_path}/st_", "").replace(
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
        y00 = list(np.cumsum(self.st.pdr_profits_OCEAN))
        s = f"Predictoor profit vs time. Current: {y00[-1]:.2f} OCEAN"

        y = "predictoor profit (OCEAN)"
        df = pd.DataFrame(y00, columns=[y])
        df["time"] = range(len(y00))

        fig = go.Figure(
            go.Scatter(x=df["time"], y=df[y], mode="lines", name="predictoor profit")
        )

        fig.add_hline(y=0, line_dash="dot", line_color="grey")
        fig.update_layout(title=s)
        fig.update_xaxes(title="time")
        fig.update_yaxes(title=y)

        return fig

    @enforce_types
    def plot_pdr_profit_vs_ptrue(self):
        avg = np.average(self.st.pdr_profits_OCEAN)
        s = f"pdr profit dist. avg={avg:.2f} OCEAN"

        y = "pdr profit (OCEAN)"
        df = pd.DataFrame(self.st.pdr_profits_OCEAN, columns=[y])
        df["prob(up)"] = self.st.probs_up

        fig = go.Figure(
            go.Scatter(x=df["prob(up)"], y=df[y], mode="markers", name="pdr profit")
        )

        fig.add_hline(y=0, line_dash="dot", line_color="grey")
        fig.update_layout(title=s)
        fig.update_xaxes(title="prob(up)")
        fig.update_yaxes(title=y)

        return fig

    @enforce_types
    def plot_trader_profit_vs_ptrue(self):
        avg = np.average(self.st.trader_profits_USD)
        s = f"trader profit dist. avg={avg:.2f} USD"

        y = "trader profit (USD)"
        df = pd.DataFrame(self.st.trader_profits_USD, columns=[y])
        df["prob(up)"] = self.st.probs_up

        fig = go.Figure(
            go.Scatter(x=df["prob(up)"], y=df[y], mode="markers", name="trader profit")
        )

        fig.add_hline(y=0, line_dash="dot", line_color="grey")
        fig.update_layout(title=s)
        fig.update_xaxes(title="prob(up)")
        fig.update_yaxes(title=y)

        return fig

    @enforce_types
    def plot_trader_profit_vs_time(self):
        y10 = list(np.cumsum(self.st.trader_profits_USD))

        s = f"Trader profit vs time. Current: ${y10[-1]:.2f}"
        y = "trader profit (USD)"
        df = pd.DataFrame(y10, columns=[y])
        df["time"] = range(len(y10))

        fig = go.Figure(
            go.Scatter(x=df["time"], y=df[y], mode="lines", name="trader profit")
        )

        fig.add_hline(y=0, line_dash="dot", line_color="grey")
        fig.update_layout(title=s)
        fig.update_xaxes(title="time")
        fig.update_yaxes(title=y)

        return fig

    @enforce_types
    def plot_model_performance_vs_time(self):
        # set titles
        clm = self.st.clm
        s1 = f"accuracy = {clm.acc_ests[-1]*100:.2f}% "
        s1 += f"[{clm.acc_ls[-1]*100:.2f}%, {clm.acc_us[-1]*100:.2f}%]"

        s2 = f"f1={clm.f1s[-1]:.4f}"
        s2 += f" [recall={clm.recalls[-1]:.4f}"
        s2 += f", precision={clm.precisions[-1]:.4f}]"

        s3 = f"log loss = {clm.losses[-1]:.4f}"

        # make subplots
        fig = make_subplots(
            rows=3,
            cols=1,
            subplot_titles=(s1, s2, s3),
            vertical_spacing=0.08,
        )

        # fill in subplots
        self._add_subplot_accuracy_vs_time(fig)  # row 1
        self._add_subplot_f1_precision_recall_vs_time(fig)  # row 2
        self._add_subplot_log_loss_vs_time(fig)  # row 3

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
    def _add_subplot_accuracy_vs_time(self, fig):
        clm = self.st.clm
        acc_ests = [100 * a for a in clm.acc_ests]
        df = pd.DataFrame(acc_ests, columns=["accuracy"])
        df["acc_ls"] = [100 * a for a in clm.acc_ls]
        df["acc_us"] = [100 * a for a in clm.acc_us]
        df["time"] = range(len(clm.acc_ests))

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
            rows=[1, 1, 1, 1],
            cols=[1, 1, 1, 1],
        )
        fig.update_yaxes(title_text="accuracy (%)", row=1, col=1)

    @enforce_types
    def _add_subplot_f1_precision_recall_vs_time(self, fig):
        clm = self.st.clm
        df = pd.DataFrame(clm.f1s, columns=["f1"])
        df["precisions"] = clm.precisions
        df["recalls"] = clm.recalls
        df["time"] = range(len(clm.f1s))

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
            rows=[2, 2, 2, 2],
            cols=[1, 1, 1, 1],
        )
        fig.update_yaxes(title_text="f1, etc", row=2, col=1)

    @enforce_types
    def _add_subplot_log_loss_vs_time(self, fig):
        clm = self.st.clm
        df = pd.DataFrame(clm.losses, columns=["log loss"])
        df["time"] = range(len(clm.losses))

        fig.add_trace(
            go.Scatter(x=df["time"], y=df["log loss"], mode="lines", name="log loss"),
            row=3,
            col=1,
        )
        fig.update_yaxes(title_text="log loss", row=3, col=1)


def file_age_in_seconds(pathname):
    stat_result = os.stat(pathname)
    return time.time() - stat_result.st_mtime
