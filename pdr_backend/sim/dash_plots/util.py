import plotly.graph_objects as go
import stopit

from pdr_backend.aimodel import aimodel_plotter
from pdr_backend.sim.dash_plots.view_elements import figure_names
from pdr_backend.sim.sim_plotter import SimPlotter


def get_figures_by_state(sim_plotter: SimPlotter, selected_vars, timeout=2):
    figures = {}

    for key in figure_names:
        if not key.startswith("aimodel"):
            with stopit.ThreadingTimeout(timeout) as context_manager:
                fig = getattr(sim_plotter, f"plot_{key}")()

            if context_manager.state == context_manager.TIMED_OUT:
                fig = go.Figure()
        else:
            with stopit.ThreadingTimeout(timeout) as context_manager:
                if key in ["aimodel_response", "aimodel_varimps"]:
                    sweep_vars = []
                    for var in selected_vars:
                        sweep_vars.append(
                            sim_plotter.aimodel_plotdata.colnames.index(var)
                        )
                    sim_plotter.aimodel_plotdata.sweep_vars = sweep_vars

                func_name = getattr(aimodel_plotter, f"plot_{key}")
                fig = func_name(sim_plotter.aimodel_plotdata)

            if context_manager.state == context_manager.TIMED_OUT:
                fig = go.Figure()

        figures[key] = fig

    return figures
