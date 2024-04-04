import time

import streamlit

from pdr_backend.aimodel import aimodel_plotter
from pdr_backend.sim.sim_plotter import SimPlotter

streamlit.set_page_config(layout="wide")

title = streamlit.empty()
inputs = streamlit.empty()
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


def load_canvas_on_state(ts):
    titletext = f"Iter #{st.iter_number} ({ts})" if ts != "final" else "Final sim state"
    title.title(titletext)

    for key in canvas:
        if not key.startswith("aimodel"):
            fig = getattr(sim_plotter, f"plot_{key}")()
        else:
            func_name = getattr(aimodel_plotter, f"plot_{key}")
            fig = func_name(sim_plotter.aimodel_plotdata)

        canvas[key].plotly_chart(fig, use_container_width=True, theme="streamlit")


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

    if new_ts == last_ts:
        time.sleep(1)
        continue

    load_canvas_on_state(new_ts)
    last_ts = new_ts

    if last_ts == "final":
        snapshots = SimPlotter.available_snapshots()
        timestamp = inputs.select_slider("Go to snapshot", snapshots, value="final")
        st, new_ts = sim_plotter.load_state(timestamp)
        load_canvas_on_state(timestamp)
        break
