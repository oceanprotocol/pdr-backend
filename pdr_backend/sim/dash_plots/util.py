from enforce_typing import enforce_types

from pdr_backend.aimodel import aimodel_plotter
from pdr_backend.sim.constants import UP
from pdr_backend.sim.dash_plots.view_elements import figure_names
from pdr_backend.sim.sim_plotter import SimPlotter

@enforce_types
def get_figures_by_state(sim_plotter: SimPlotter, selected_vars):
    figures = {}

    for key in figure_names:
        if not key.startswith("aimodel"):
            fig = getattr(sim_plotter, f"plot_{key}")()
        else:
            if key in ["aimodel_response", "aimodel_varimps"]:
                sweep_vars = []
                for var in selected_vars:
                    sweep_vars.append(sim_plotter.aimodel_plotdata[UP].colnames.index(var))
                sim_plotter.aimodel_plotdata[UP].sweep_vars = sweep_vars

            func_name = getattr(aimodel_plotter, f"plot_{key}")
            fig = func_name(sim_plotter.aimodel_plotdata[UP])

        figures[key] = fig

    return figures
