import time

from dash import Input, Output, State

from pdr_backend.sim.dash_plots.util import get_figures_by_state
from pdr_backend.sim.dash_plots.view_elements import (
    arrange_figures,
    get_header_elements,
    get_waiting_template,
    non_final_state_div,
    selected_var_checklist,
    snapshot_slider,
)
from pdr_backend.sim.sim_plotter import SimPlotter


def wait_for_state(sim_plotter, run_id, set_ts):
    for _ in range(5):
        try:
            st, ts = sim_plotter.load_state(run_id, set_ts)
            return st, ts
        except Exception as e:
            if "out of input" in str(e):
                time.sleep(0.1)
                continue

            raise e


def get_callbacks(app):
    @app.callback(
        Output("interval-component", "disabled"),
        [Input("sim_current_ts", "className")],
        [State("interval-component", "disabled")],
    )
    # pylint: disable=unused-argument
    def callback_func_start_stop_interval(value, disabled_state):
        # stop refreshing if final state was reached
        return value == "finalState"

    @app.callback(
        Output("selected_vars", "value"),
        Input("aimodel_varimps", "clickData"),
        State("selected_vars", "value"),
    )
    def update_selected_vars(clickData, selected_vars):
        if clickData is None:
            return selected_vars

        label = clickData["points"][0]["y"]
        if label in selected_vars:
            selected_vars.remove(label)
        else:
            selected_vars.append(label)

        return selected_vars

    @app.callback(
        Output("live-graphs", "children"),
        Input("interval-component", "n_intervals"),
        Input("selected_vars", "value"),
        Input("state_slider", "value"),
        State("selected_vars", "value"),
    )
    # pylint: disable=unused-argument
    def update_graph_live(n, selected_vars, slider_value, selected_vars_old):
        run_id = app.run_id if app.run_id else SimPlotter.get_latest_run_id()
        set_ts = None

        if slider_value is not None:
            snapshots = SimPlotter.available_snapshots(run_id)
            set_ts = snapshots[slider_value]

        sim_plotter = SimPlotter()

        try:
            st, ts = wait_for_state(sim_plotter, run_id, set_ts)
        except Exception as e:
            return [get_waiting_template(e)]

        elements = get_header_elements(run_id, st, ts)

        slider = (
            snapshot_slider(run_id, set_ts, slider_value)
            if ts == "final"
            else non_final_state_div
        )
        elements.append(slider)

        state_options = sim_plotter.aimodel_plotdata.colnames
        elements.append(selected_var_checklist(state_options, selected_vars_old))

        figures = get_figures_by_state(sim_plotter, selected_vars)
        elements = elements + arrange_figures(figures)

        return elements
