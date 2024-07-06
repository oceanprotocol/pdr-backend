#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import List

from enforce_typing import enforce_types
import plotly.graph_objects as go
import stopit

from pdr_backend.aimodel import aimodel_plotter
from pdr_backend.grpmodel.constants import Dirn, UP, DOWN
from pdr_backend.sim.dash_plots.view_elements import (
    FIGURE_NAMES,
    OTHER_FIGURES,
    MODEL_RESPONSE_FIGURES,
)
from pdr_backend.sim.sim_plotter import SimPlotter


@enforce_types
def get_figures_by_state(
    sim_plotter: SimPlotter,
    selected_vars_UP: List[str],  # UP model selected varnames
    selected_vars_DOWN: List[str],  # DOWN ""
    timeout: int = 2,
):
    figs = {}

    for fig_name in FIGURE_NAMES:
        if fig_name in OTHER_FIGURES:
            with stopit.ThreadingTimeout(timeout) as context_manager:
                fig = getattr(sim_plotter, f"plot_{fig_name}")()

        elif fig_name in MODEL_RESPONSE_FIGURES:
            with stopit.ThreadingTimeout(timeout) as context_manager:
                dirn = UP if "UP" in fig_name else DOWN
                aimodel_plotdata = sim_plotter.aimodel_plotdata[dirn]
                colnames = aimodel_plotdata.colnames
                sel_vars = _sel_vars(dirn, selected_vars_UP, selected_vars_DOWN)
                sel_Is = [colnames.index(var) for var in sel_vars]
                aimodel_plotdata.sweep_vars = sel_Is
                func_name = _func_name(fig_name)
                func = getattr(aimodel_plotter, func_name)
                fig = func(aimodel_plotdata)

        else:
            raise ValueError(fig_name)

        if context_manager.state == context_manager.TIMED_OUT:
            fig = go.Figure()

        figs[fig_name] = fig

    return figs


@enforce_types
def _sel_vars(dirn: Dirn, sel_vars_UP, sel_vars_DOWN) -> List[str]:
    if dirn == UP:
        return sel_vars_UP
    return sel_vars_DOWN


@enforce_types
def _func_name(fig_name: str) -> str:
    return f"plot_{fig_name}".replace("_UP", "").replace("_DOWN", "")
