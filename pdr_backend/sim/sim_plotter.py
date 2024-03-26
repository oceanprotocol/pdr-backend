import altair as alt
import numpy as np
import pandas as pd
from enforce_typing import enforce_types

from pdr_backend.aimodel.aimodel_plotdata import AimodelPlotdata
from datetime import datetime
import pickle
import os
import glob


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

    def load_state(self):
        if not os.path.exists("sim_state"):
            raise Exception("sim_state folder does not exist. Please run the simulation first.")

        if not os.path.exists("sim_state/st_final.pkl"):
            # TODO logger.info("Simulation still running. Plot will update in real time")
            latest_file = max(glob.glob('sim_state/st_*.pkl'))
            self.st = pickle.load(open(latest_file, "rb"))
            self.aimodel_plotdata = pickle.load(open(latest_file.replace("st_", "aimodel_plotdata_"), "rb"))
            return self.st, latest_file.replace("sim_state/st_", "").replace(".pkl", "")

        # TODO: logger.info("Simulation finished. Plotting final results")
        self.st = pickle.load(open("sim_state/st_final.pkl", "rb"))
        self.aimodel_plotdata = pickle.load(open("sim_state/aimodel_plotdata_final.pkl", "rb"))
        return self.st, "final"

    def init_state(self):
        files = glob.glob('sim_state/*')
        for f in files:
            os.remove(f)

    def save_state(self, sim_state, aimodel_plotdata: AimodelPlotdata, is_final: bool = False):
        # TODO: for multisim, we could add a unique identifier to the filename and separate states
        ts = datetime.now().strftime("%Y%m%d_%H%M%S.%f")[:-3] if not is_final else "final"
        pickle.dump(sim_state, open(f"sim_state/st_{ts}.pkl", "wb"))
        pickle.dump(aimodel_plotdata, open(f"sim_state/aimodel_plotdata_{ts}.pkl", "wb"))

    @enforce_types
    def plot_pdr_profit_vs_time(self):
        y00 = list(np.cumsum(self.st.pdr_profits_OCEAN))
        s = f"Predictoor profit vs time. Current: {y00[-1]:.2f} OCEAN"

        y = "predictoor profit (OCEAN)"
        df = pd.DataFrame(y00, columns=[y])
        df["time"] = range(len(y00))

        chart = (
            alt.Chart(df, title=s)
            .mark_line()
            .encode(
                x="time",
                y=y,
            )
            .interactive()
        )

        ref_line = (
            alt.Chart(pd.DataFrame({y: [0]}))
            .mark_rule(color="grey", strokeDash=[10, 10])
            .encode(y=y)
        )

        return chart + ref_line

    @enforce_types
    def plot_trader_profit_vs_time(self):
        y10 = list(np.cumsum(self.st.trader_profits_USD))

        s = f"Trader profit vs time. Current: ${y10[-1]:.2f}"
        y = "trader profit (USD)"
        df = pd.DataFrame(y10, columns=[y])
        df["time"] = range(len(y10))
        chart = (
            alt.Chart(df, title=s)
            .mark_line()
            .encode(
                x="time",
                y=y,
            )
            .interactive()
        )

        ref_line = (
            alt.Chart(pd.DataFrame({y: [0]}))
            .mark_rule(color="grey", strokeDash=[10, 10])
            .encode(y=y)
        )

        return chart + ref_line

    @enforce_types
    def plot_accuracy_vs_time(self):
        clm = self.st.clm
        s = f"accuracy = {clm.acc_ests[-1]*100:.2f}% "
        s += f"[{clm.acc_ls[-1]*100:.2f}%, {clm.acc_us[-1]*100:.2f}%]"

        y = "% correct (lower, upper bound)"
        acc_ests = [100 * a for a in clm.acc_ests]
        df = pd.DataFrame(acc_ests, columns=[y])
        df["acc_ls"] = [100 * a for a in clm.acc_ls]
        df["acc_us"] = [100 * a for a in clm.acc_us]
        df["time"] = range(len(clm.acc_ests))

        chart = (
            alt.Chart(df, title=s)
            .mark_line()
            .encode(x="time", y=y, color=alt.value("darkblue"))
        )

        ref_line = (
            alt.Chart(pd.DataFrame({y: [50]}))
            .mark_rule(color="grey", strokeDash=[10, 10])
            .encode(y=y)
        )

        area_chart = (
            alt.Chart(df)
            .mark_area()
            .encode(
                x="time",
                y=alt.Y("acc_ls", title=y),
                y2="acc_us",
                color=alt.value("lightblue"),
            )
        )

        return area_chart + ref_line + chart

    @enforce_types
    def plot_f1_precision_recall_vs_time(self):
        clm = self.st.clm
        s = f"f1={clm.f1s[-1]:.4f}"
        s += f" [recall={clm.recalls[-1]:.4f}"
        s += f", precision={clm.precisions[-1]:.4f}]"

        y = "% correct (lower, upper bound)"
        df = pd.DataFrame(clm.f1s, columns=["f1"])
        df["precisions"] = clm.precisions
        df["recalls"] = clm.recalls
        df["time"] = range(len(clm.f1s))

        data_long = pd.melt(
            df,
            id_vars=["time"],
            value_vars=["f1", "precisions", "recalls"],
            var_name="var",
            value_name="f1,precisions,recalls",
        )

        chart = (
            alt.Chart(data_long)
            .mark_line()
            .encode(
                x="time",
                y=alt.Y("f1,precisions,recalls", title=y),
                color="var:N",  # Use the category field for color encoding
            )
            .properties(title=s)
        )

        ref_line = (
            alt.Chart(pd.DataFrame({y: [0.5]}))
            .mark_rule(color="grey", strokeDash=[10, 10])
            .encode(y=y)
        )

        return chart + ref_line

    @enforce_types
    def plot_pdr_profit_vs_ptrue(self):
        avg = np.average(self.st.pdr_profits_OCEAN)
        s = f"pdr profit dist. avg={avg:.2f} OCEAN"

        y = "pdr profit (OCEAN)"
        df = pd.DataFrame(self.st.pdr_profits_OCEAN, columns=[y])
        df["prob(up)"] = self.st.probs_up

        chart = alt.Chart(df, title=s).mark_circle().encode(x="prob(up)", y=y)

        ref_line = (
            alt.Chart(pd.DataFrame({y: [0]}))
            .mark_rule(color="grey", strokeDash=[10, 10])
            .encode(y=y)
        )

        return chart + ref_line

    @enforce_types
    def plot_trader_profit_vs_ptrue(self):
        avg = np.average(self.st.trader_profits_USD)
        s = f"trader profit dist. avg={avg:.2f} USD"

        y = "trader profit (USD)"
        df = pd.DataFrame(self.st.trader_profits_USD, columns=[y])
        df["prob(up)"] = self.st.probs_up

        chart = alt.Chart(df, title=s).mark_circle().encode(x="prob(up)", y=y)

        ref_line = (
            alt.Chart(pd.DataFrame({y: [0]}))
            .mark_rule(color="grey", strokeDash=[10, 10])
            .encode(y=y)
        )

        return chart + ref_line
