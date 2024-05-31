import time

from dash import Input, Output, State

from pdr_backend.sim.dash_plots.util import get_figures_by_state
from pdr_backend.sim.dash_plots.view_elements import (
    arrange_figures,
    get_header_elements,
    get_waiting_template,
    selected_var_checklist,
    get_tabs_component,
)
from pdr_backend.sim.sim_plotter import SimPlotter


def wait_for_state(sim_plotter, run_id):
    for _ in range(5):
        try:
            st, ts = sim_plotter.load_state(run_id)
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
        Output("tabs-container", "children"),
        Output("header", "children"),
        Input("interval-component", "n_intervals"),
        Input("selected_vars", "value"),
        State("selected_vars", "value"),
    )
    # pylint: disable=unused-argument
    def update_graph_live(n, selected_vars, selected_vars_old):
        run_id = app.run_id if app.run_id else SimPlotter.get_latest_run_id()
        sim_plotter = SimPlotter()

        try:
            st, ts = wait_for_state(sim_plotter, run_id)
        except Exception as e:
            return [get_waiting_template(e)]

        header = get_header_elements(run_id, st, ts)
        elements = []

        state_options = sim_plotter.aimodel_plotdata.colnames
        elements.append(selected_var_checklist(state_options, selected_vars_old))

        figures = get_figures_by_state(sim_plotter, selected_vars)
        aranged_figures = arrange_figures(figures)
        tabs = [
            {"name": "Profit", "components": [aranged_figures[0], aranged_figures[2]]},
            {
                "name": "Model performance",
                "components": [aranged_figures[1], aranged_figures[4]],
            },
            {"name": "Model response", "components": [aranged_figures[3]]},
        ]
        elements = elements + [get_tabs_component(tabs)]

        return elements, header
