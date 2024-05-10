from unittest.mock import Mock, patch

from plotly.graph_objs import Figure

from pdr_backend.sim.dash_plots.util import get_figures_by_state
from pdr_backend.sim.dash_plots.view_elements import (
    arrange_figures,
    figure_names,
    get_header_elements,
    get_waiting_template,
    prune_snapshots,
    selected_var_checklist,
    snapshot_slider,
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


def test_arrange_figures():
    figures = {key: Figure() for key in figure_names}
    result = arrange_figures(figures)
    seen = set()
    for div in result:
        for graph in div.children:
            if hasattr(graph, "id"):
                seen.add(graph.id)

    assert len(seen) == len(figure_names)


def test_snapshot_slider():
    with patch(
        "pdr_backend.sim.dash_plots.view_elements.prune_snapshots"
    ) as mock_prune_snapshots:
        mock_prune_snapshots.return_value = ["ts1", "ts2", "final"]

    result = snapshot_slider("abcd", "ts1", 1)
    assert result


def test_prune_snapshots():
    with patch(
        "pdr_backend.sim.dash_plots.view_elements.SimPlotter.available_snapshots"
    ) as mock_snapshots:
        mock_snapshots.return_value = ["ts1", "ts2", "final"]
        assert prune_snapshots("abcd") == ["ts1", "ts2"]

    more_than_50 = [f"ts{i}" for i in range(100)] + ["final"]
    with patch(
        "pdr_backend.sim.dash_plots.view_elements.SimPlotter.available_snapshots"
    ) as mock_snapshots:
        mock_snapshots.return_value = more_than_50
        assert prune_snapshots("abcd") == [f"ts{i}" for i in range(100) if i % 2 == 0]


def test_selected_var_checklist():
    result = selected_var_checklist(["var1", "var2"], ["var1"])
    assert result.value == ["var1"]
    assert result.options[0]["label"] == "var1"
    assert result.options[1]["label"] == "var2"


def test_get_figures_by_state():
    mock_sim_plotter = Mock(spec=SimPlotter)
    mock_sim_plotter.plot_pdr_profit_vs_time.return_value = Figure()
    mock_sim_plotter.plot_trader_profit_vs_time.return_value = Figure()
    mock_sim_plotter.plot_accuracy_vs_time.return_value = Figure()
    mock_sim_plotter.plot_pdr_profit_vs_ptrue.return_value = Figure()
    mock_sim_plotter.plot_trader_profit_vs_ptrue.return_value = Figure()
    mock_sim_plotter.plot_f1_precision_recall_vs_time.return_value = Figure()
    mock_sim_plotter.plot_log_loss_vs_time.return_value = Figure()

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
