#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import time

from dash import Input, Output, State

from pdr_backend.grpmodel.constants import UP
from pdr_backend.sim.dash_plots.util import get_figures_by_state
from pdr_backend.sim.dash_plots.view_elements import (
    get_tabs,
    get_header_elements,
    get_waiting_template,
    selected_var_UP_checklist,
    selected_var_DOWN_checklist,
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
        Output("selected_vars_UP", "value"),
        Input("aimodel_varimps_UP", "clickData"),
        State("selected_vars_UP", "value"),
    )
    def update_selected_vars_UP(clickData, selected_vars_UP):
        if clickData is None:
            return selected_vars_UP

        label = clickData["points"][0]["y"]
        if label in selected_vars_UP:
            selected_vars_UP.remove(label)
        else:
            selected_vars_UP.append(label)

        return selected_vars_UP

    @app.callback(
        Output("selected_vars_DOWN", "value"),
        Input("aimodel_varimps_DOWN", "clickData"),
        State("selected_vars_DOWN", "value"),
    )
    def update_selected_vars_DOWN(clickData, selected_vars_DOWN):
        if clickData is None:
            return selected_vars_DOWN

        label = clickData["points"][0]["y"]
        if label in selected_vars_DOWN:
            selected_vars_DOWN.remove(label)
        else:
            selected_vars_DOWN.append(label)

        return selected_vars_DOWN

    @app.callback(
        Output("tabs-container", "children"),
        Output("header", "children"),
        Input("interval-component", "n_intervals"),
        Input("selected_vars_UP", "value"),
        Input("selected_vars_DOWN", "value"),
        State("selected_vars_UP", "value"),
        State("selected_vars_DOWN", "value"),
        State("selected-tab", "data"),
    )
    # pylint: disable=unused-argument
    def update_graph_live(
        n,
        selected_vars_UP,
        selected_vars_DOWN,
        selected_vars_UP_old,
        selected_vars_DOWN_old,
        selected_tab,
    ):
        try:
            run_id = app.run_id if app.run_id else SimPlotter.get_latest_run_id()
            sim_plotter = SimPlotter()
            st, ts = wait_for_state(sim_plotter, run_id)
        except Exception as e:
            return [], [get_waiting_template(e)]

        header = get_header_elements(run_id, st, ts)
        elements = []

        state_options = sim_plotter.aimodel_plotdata[UP].colnames

        cU = selected_var_UP_checklist(state_options, selected_vars_UP_old)
        cD = selected_var_DOWN_checklist(state_options, selected_vars_DOWN_old)
        elements += [cU, cD]

        timeout = 2 if ts != "final" or n < 2 else 10
        figures = get_figures_by_state(
            sim_plotter,
            selected_vars_UP,
            selected_vars_DOWN,
            timeout,
        )

        tabs = get_tabs(figures)
        selected_tab_value = selected_tab if selected_tab else tabs[0]["name"]
        elements = elements + [get_tabs_component(tabs, selected_tab_value)]

        return elements, header

    @app.callback(Output("selected-tab", "data"), Input("tabs", "value"))
    # pylint: disable=unused-argument
    def update_selected_tab_state(selected_tab):
        return selected_tab
