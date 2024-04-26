from dash import Input, Output, State

from pdr_backend.sim.sim_plotter import SimPlotter
from pdr_dash_plots.view_elements import (
    arrange_figures,
    empty_slider_div,
    get_header_elements,
    get_waiting_template,
    snapshot_slider,
)
from pdr_dash_plots.util import get_figures_by_state, get_latest_run_id


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
        Output("live-graphs", "children"),
        Input("interval-component", "n_intervals"),
        Input("aimodel_varimps", "clickData"),
        Input("state_slider", "value"),
    )
    # pylint: disable=unused-argument
    def update_graph_live(n, clickData, slider_value):
        run_id = app.run_id if app.run_id else get_latest_run_id()
        set_ts = None

        if slider_value is not None:
            snapshots = SimPlotter.available_snapshots(run_id)
            set_ts = snapshots[slider_value]

        sim_plotter = SimPlotter()

        try:
            st, ts = sim_plotter.load_state(run_id, set_ts)
        except Exception as e:
            return [get_waiting_template(e)]

        elements = get_header_elements(run_id, st, ts)

        slider = (
            snapshot_slider(run_id, set_ts, slider_value)
            if ts == "final"
            else empty_slider_div
        )
        elements.append(slider)

        figures = get_figures_by_state(sim_plotter, clickData)
        elements = elements + arrange_figures(figures)

        return elements
