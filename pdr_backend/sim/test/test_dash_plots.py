from unittest.mock import Mock, patch

from plotly.graph_objs import Figure

from pdr_backend.sim.dash_plots.util import get_figures_by_state
from pdr_backend.sim.dash_plots.view_elements import (
    get_tabs,
    figure_names,
    get_header_elements,
    get_waiting_template,
    selected_var_checklist,
)
from pdr_backend.sim.sim_plotter import SimPlotter


def test_get_waiting_template():
    result = get_waiting_template("custom message")
    assert "custom message" in result.children[0].children


def test_get_header_elements():
    st = Mock()
    st.iter_number = 5

    result = get_header_elements("abcd", st, "ts")
    assert "Simulation ID: abcd" in result[0].children
    assert "Iter #5 (ts)" in result[1].children
    assert result[1].className == "runningState"

    result = get_header_elements("abcd", st, "final")
    assert "Simulation ID: abcd" in result[0].children
    assert "Final sim state" in result[1].children
    assert result[1].className == "finalState"


def test_get_tabs():
    figures = {key: Figure() for key in figure_names}
    result = get_tabs(figures)
    for tab in result:
        assert "name" in tab
        assert "components" in tab


def test_selected_var_checklist():
    result = selected_var_checklist(["var1", "var2"], ["var1"])
    assert result.value == ["var1"]
    assert result.options[0]["label"] == "var1"
    assert result.options[1]["label"] == "var2"


def test_get_figures_by_state():
    mock_sim_plotter = Mock(spec=SimPlotter)
    mock_sim_plotter.plot_pdr_profit_vs_time.return_value = Figure()
    mock_sim_plotter.plot_trader_profit_vs_time.return_value = Figure()
    mock_sim_plotter.plot_pdr_profit_vs_ptrue.return_value = Figure()
    mock_sim_plotter.plot_trader_profit_vs_ptrue.return_value = Figure()
    mock_sim_plotter.plot_model_performance_vs_time.return_value = Figure()
    mock_sim_plotter.plot_prediction_residuals.return_value = Figure()

    plotdata = Mock()
    plotdata.colnames = ["var1", "var2"]

    mock_sim_plotter.aimodel_plotdata = plotdata

    with patch(
        "pdr_backend.sim.dash_plots.util.aimodel_plotter"
    ) as mock_aimodel_plotter:
        mock_aimodel_plotter.plot_aimodel_response.return_value = Figure()
        mock_aimodel_plotter.plot_aimodel_varimps.return_value = Figure()

        result = get_figures_by_state(mock_sim_plotter, ["var1", "var2"])

    for key in figure_names:
        assert key in result
        assert isinstance(result[key], Figure)
