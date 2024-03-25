import altair as alt
import numpy as np
import pandas as pd
import streamlit
from enforce_typing import enforce_types

from pdr_backend.aimodel.aimodel_plotdata import AimodelPlotdata
from pdr_backend.aimodel.aimodel_plotter import (
    plot_aimodel_response,
    plot_aimodel_varimps,
)
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.sim.sim_state import SimState

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

        c1, c2, c3 = streamlit.columns((1, 1, 2))
        c4, c5 = streamlit.columns((1, 1))
        c6, c7 = streamlit.columns((1, 1))
        c8, _ = streamlit.columns((1, 1))

        self.canvas = {
            "pdr_profit_vs_time": c1.empty(),
            "trader_profit_vs_time": c2.empty(),
            "accuracy_vs_time": c3.empty(),
            "pdr_profit_vs_ptrue": c4.empty(),
            "trader_profit_vs_ptrue": c5.empty(),
            "aimodel_varimps": c6.empty(),
            "aimodel_response": c7.empty(),
            "f1_precision_recall_vs_time": c8.empty(),
        }

    # pylint: disable=too-many-statements
    @enforce_types
    def compute_plot(self, aimodel_plotdata: AimodelPlotdata) -> None:
        """
        @description
          Create / update whole plot, with many subplots

        @arguments
          aimodel_plotdata -- has model, X_train, etc
        """
        # main work: create/update subplots
        self._plot_pdr_profit_vs_time()
        self._plot_trader_profit_vs_time()

        self._plot_accuracy_vs_time()
        self._plot_f1_precision_recall_vs_time()
        self._plot_pdr_profit_vs_ptrue()
        self._plot_trader_profit_vs_ptrue()

        self._plot_aimodel_varimps(aimodel_plotdata)
        self._plot_aimodel_response(aimodel_plotdata)

    @enforce_types
    def _plot_pdr_profit_vs_time(self):
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

        self.canvas["pdr_profit_vs_time"].altair_chart(
            chart + ref_line, use_container_width=True, theme="streamlit"
        )

    @enforce_types
    def _plot_trader_profit_vs_time(self):
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

        self.canvas["trader_profit_vs_time"].altair_chart(
            chart + ref_line, use_container_width=True, theme="streamlit"
        )

    @enforce_types
    def _plot_accuracy_vs_time(self):
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

        self.canvas["accuracy_vs_time"].altair_chart(
            area_chart + ref_line + chart, use_container_width=True, theme="streamlit"
        )

    @enforce_types
    def _plot_f1_precision_recall_vs_time(self):
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

        self.canvas["f1_precision_recall_vs_time"].altair_chart(
            chart + ref_line, use_container_width=True, theme="streamlit"
        )

    @enforce_types
    def _plot_pdr_profit_vs_ptrue(self):
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

        self.canvas["pdr_profit_vs_ptrue"].altair_chart(
            chart + ref_line, use_container_width=True, theme="streamlit"
        )

    @enforce_types
    def _plot_trader_profit_vs_ptrue(self):
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

        self.canvas["trader_profit_vs_ptrue"].altair_chart(
            chart + ref_line, use_container_width=True, theme="streamlit"
        )

    @enforce_types
    def _plot_aimodel_varimps(self, d: AimodelPlotdata):
        chart = plot_aimodel_varimps(d)
        self.canvas["aimodel_varimps"].altair_chart(
            chart, use_container_width=True, theme="streamlit"
        )

    @enforce_types
    def _plot_aimodel_response(self, d: AimodelPlotdata):
        chart = plot_aimodel_response(d)
        self.canvas["aimodel_response"].plotly_chart(
            chart, use_container_width=True, theme="streamlit"
        )


@enforce_types
def _slice(a: list, N_done: int, N: int, mult: float = 1.0) -> list:
    return [a[i] * mult for i in range(max(0, N_done - 1), N)]
