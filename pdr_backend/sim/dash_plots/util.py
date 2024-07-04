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
def get_figures_by_state(sim_plotter: SimPlotter, selected_vars: list):
    figures = {}

    for figure_name in FIGURE_NAMES:
        if figure_name in OTHER_FIGURES:
            fig = getattr(sim_plotter, f"plot_{figure_name}")()

        elif figure_name in MODEL_RESPONSE_FIGURES:
            dirn = _figure_name_to_dirn(figure_name)
            aimodel_plotdata = sim_plotter.aimodel_plotdata[dirn]
            sweep_vars = [aimodel_plotdata.colnames.index(varname)
                          for varname in selected_vars]
            aimodel_plotdata.sweep_vars = sweep_vars
            func_name = _figure_name_to_func_name(figure_name)
            func = getattr(aimodel_plotter, func_name)
            fig = func(aimodel_plotdata)

        else:
            raise ValueError(figure_name)

        figures[figure_name] = fig

    return figures

@enforce_types
def _figure_name_to_dirn(figure_name: str) -> Dirn:
    if "UP" in figure_name:
        return UP
    if "DOWN" in figure_name:
        return DOWN
    raise ValueError(figure_name)

@enforce_types
def _figure_name_to_func_name(figure_name: str) -> Dirn:
    return f"plot_{figure_name}".replace("_UP","").replace("_DOWN","")
