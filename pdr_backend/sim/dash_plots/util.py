from typing import List

from enforce_typing import enforce_types

from pdr_backend.aimodel import aimodel_plotter
from pdr_backend.sim.constants import UP
from pdr_backend.sim.dash_plots.view_elements import (
    FIGURE_NAMES,
    OTHER_FIGURES,
    MODEL_RESPONSE_FIGURES,
)
from pdr_backend.sim.sim_plotter import SimPlotter
from pdr_backend.sim.constants import Dirn, UP, DOWN


@enforce_types
def get_figures_by_state(
    sim_plotter: SimPlotter,
    selected_vars_UP: List[str],  # UP model selected varnames
    selected_vars_DOWN: List[str],  # DOWN ""
):
    figs = {}

    for fig_name in FIGURE_NAMES:
        if fig_name in OTHER_FIGURES:
            fig = getattr(sim_plotter, f"plot_{fig_name}")()

        elif fig_name in MODEL_RESPONSE_FIGURES:
            dirn = UP if "UP" in fig_name else DOWN
            aimodel_plotdata = sim_plotter.aimodel_plotdata[dirn]
            selected_vars = selected_vars_UP if dirn == UP else selected_vars_DOWN
            selected_Is = [
                aimodel_plotdata.colnames.index(var) for var in selected_vars
            ]
            aimodel_plotdata.sweep_vars = selected_Is
            func_name = f"plot_{fig_name}".replace("_UP", "").replace("_DOWN", "")
            func = getattr(aimodel_plotter, func_name)
            fig = func(aimodel_plotdata)

        else:
            raise ValueError(fig_name)

        figs[fig_name] = fig

    return figs
