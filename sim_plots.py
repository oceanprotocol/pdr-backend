import time

import streamlit

from pdr_backend.aimodel.aimodel_plotter import (
    plot_aimodel_response,
    plot_aimodel_varimps,
)
from pdr_backend.sim.sim_plotter import SimPlotter

streamlit.set_page_config(layout="wide")

title = streamlit.empty()
c1, c2, c3 = streamlit.columns((1, 1, 2))
c4, c5 = streamlit.columns((1, 1))
c6, c7 = streamlit.columns((1, 1))
c8, _ = streamlit.columns((1, 1))

canvas = {
    "pdr_profit_vs_time": c1.empty(),
    "trader_profit_vs_time": c2.empty(),
    "accuracy_vs_time": c3.empty(),
    "pdr_profit_vs_ptrue": c4.empty(),
    "trader_profit_vs_ptrue": c5.empty(),
    "aimodel_varimps": c6.empty(),
    "aimodel_response": c7.empty(),
    "f1_precision_recall_vs_time": c8.empty(),
}

last_ts = None
sim_plotter = SimPlotter()

while True:
    try:
        sim_plotter.load_state()
        break
    except Exception as e:
        time.sleep(3)
        title.title(f"Waiting for sim state... {e}")
        continue

while True:
    try:
        st, new_ts = sim_plotter.load_state()
    except EOFError:
        time.sleep(1)
        continue

    title.title(f"Iter #{st.iter_number} ({new_ts})")

    if new_ts == last_ts:
        time.sleep(1)
        continue

    canvas["pdr_profit_vs_time"].plotly_chart(
        sim_plotter.plot_pdr_profit_vs_time(),
        use_container_width=True,
        theme="streamlit",
    )

    canvas["trader_profit_vs_time"].plotly_chart(
        sim_plotter.plot_trader_profit_vs_time(),
        use_container_width=True,
        theme="streamlit",
    )

    canvas["accuracy_vs_time"].plotly_chart(
        sim_plotter.plot_accuracy_vs_time(), use_container_width=True, theme="streamlit"
    )

    canvas["f1_precision_recall_vs_time"].altair_chart(
        sim_plotter.plot_f1_precision_recall_vs_time(),
        use_container_width=True,
        theme="streamlit",
    )

    canvas["pdr_profit_vs_ptrue"].altair_chart(
        sim_plotter.plot_pdr_profit_vs_ptrue(),
        use_container_width=True,
        theme="streamlit",
    )

    canvas["trader_profit_vs_ptrue"].altair_chart(
        sim_plotter.plot_trader_profit_vs_ptrue(),
        use_container_width=True,
        theme="streamlit",
    )

    canvas["aimodel_varimps"].altair_chart(
        plot_aimodel_varimps(sim_plotter.aimodel_plotdata),
        use_container_width=True,
        theme="streamlit",
    )

    canvas["aimodel_response"].plotly_chart(
        plot_aimodel_response(sim_plotter.aimodel_plotdata),
        use_container_width=True,
        theme="streamlit",
    )

    last_ts = new_ts

    if last_ts == "final":
        title.title("Final sim state")
        break
