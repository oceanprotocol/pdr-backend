import os
from pathlib import Path

from pdr_backend.aimodel import aimodel_plotter
from pdr_backend.sim.sim_plotter import SimPlotter
from pdr_dash_plots.view_elements import figure_names


def get_latest_run_id():
    path = sorted(Path("sim_state").iterdir(), key=os.path.getmtime)[-1]
    return str(path).replace("sim_state/", "")


def get_all_run_names():
    path = Path("sim_state").iterdir()
    return [str(p).replace("sim_state/", "") for p in path]


def get_figures_by_state(sim_plotter: SimPlotter, selected_vars):
    figures = {}

    for key in figure_names:
        if not key.startswith("aimodel"):
            fig = getattr(sim_plotter, f"plot_{key}")()
        else:
            if key in ["aimodel_response", "aimodel_varimps"]:
                sweep_vars = []
                for var in selected_vars:
                    sweep_vars.append(sim_plotter.aimodel_plotdata.colnames.index(var))
                sim_plotter.aimodel_plotdata.sweep_vars = sweep_vars

            func_name = getattr(aimodel_plotter, f"plot_{key}")
            fig = func_name(sim_plotter.aimodel_plotdata)

        figures[key] = fig

    return figures
