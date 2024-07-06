#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from unittest.mock import Mock, patch

from enforce_typing import enforce_types
from plotly.graph_objs import Figure

from pdr_backend.binmodel.constants import UP, DOWN
from pdr_backend.sim.dash_plots.util import get_figures_by_state
from pdr_backend.sim.dash_plots.view_elements import (
    FIGURE_NAMES,
    get_header_elements,
    get_tabs,
    get_waiting_template,
    selected_var_UP_checklist,
    selected_var_DOWN_checklist,
)
from pdr_backend.sim.sim_plotter import SimPlotter


@enforce_types
def test_get_waiting_template():
    result = get_waiting_template("custom message")
    assert "custom message" in result.children[0].children


@enforce_types
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


@enforce_types
def test_get_tabs():
    figures = {name: Figure() for name in FIGURE_NAMES}
    result = get_tabs(figures)
    for tab in result:
        assert "name" in tab
        assert "components" in tab


@enforce_types
def test_selected_var_UP_checklist():
    result = selected_var_UP_checklist(["var_up1", "var_up2"], ["var_up1"])
    assert result.value == ["var_up1"]
    assert result.options[0]["label"] == "var_up1"
    assert result.options[1]["label"] == "var_up2"


@enforce_types
def test_selected_var_DOWN_checklist():
    result = selected_var_DOWN_checklist(["var_down1", "var_down2"], ["var_down1"])
    assert result.value == ["var_down1"]
    assert result.options[0]["label"] == "var_down1"
    assert result.options[1]["label"] == "var_down2"


@enforce_types
def test_get_figures_by_state():
    mock_sim_plotter = Mock(spec=SimPlotter)
    mock_sim_plotter.plot_pdr_profit_vs_time.return_value = Figure()
    mock_sim_plotter.plot_trader_profit_vs_time.return_value = Figure()
    mock_sim_plotter.plot_pdr_profit_vs_ptrue.return_value = Figure()
    mock_sim_plotter.plot_trader_profit_vs_ptrue.return_value = Figure()
    mock_sim_plotter.plot_model_performance_vs_time.return_value = Figure()

    plotdata = {UP: Mock(), DOWN: Mock()}
    plotdata[UP].colnames = ["var_up1", "var_up2"]
    plotdata[DOWN].colnames = ["var_down1", "var_down2"]

    mock_sim_plotter.aimodel_plotdata = plotdata

    with patch(
        "pdr_backend.sim.dash_plots.util.aimodel_plotter"
    ) as mock_aimodel_plotter:
        # *not* with UP or DOWN here, because the plot_*_() calls input Dirn
        mock_aimodel_plotter.plot_aimodel_response.return_value = Figure()
        mock_aimodel_plotter.plot_aimodel_varimps.return_value = Figure()

        figs = get_figures_by_state(
            mock_sim_plotter,
            ["var_up1", "var_up2"],
            ["var_down1", "var_down2"],
        )

    assert sorted(figs.keys()) == sorted(FIGURE_NAMES)
    for fig_name in FIGURE_NAMES:
        assert fig_name in figs
        assert isinstance(figs[fig_name], Figure)
