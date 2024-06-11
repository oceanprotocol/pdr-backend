from dash import dcc, html
from plotly.graph_objs import Figure

from pdr_backend.statutil.dash_plots.view_elements import (
    get_graphs_container,
    display_plots_view,
    display_on_column_graphs,
    get_column_graphs,
    get_input_elements,
)


def test_display_plots_view():
    col1 = html.Div(id="column1")
    col2 = html.Div(id="column2")
    columns = [col1, col2]
    result = display_plots_view(columns)
    assert len(columns) == len(result.children)
    assert "column1" in result.children[0].id
    assert "column2" in result.children[1].id


def test_get_column_graphs():
    fig1 = Figure([])
    fig2 = Figure([])
    figure_data = [
        {"id_parent": "fig1_graph", "fig": fig1, "graph_id": "fig1_graph"},
        {"id_parent": "fig2_graph", "fig": fig2, "graph_id": "fig2_graph"},
    ]
    result = get_column_graphs("fig1_graph", figure_data, "title1", "")
    assert len(result) == 1
    assert len(result[0].children) == len(figure_data) + 2
    assert figure_data[0]["id_parent"] + "-title" == result[0].children[0].id
    assert figure_data[0]["id_parent"] == result[0].children[2].id
    assert figure_data[1]["id_parent"] == result[0].children[3].id


def test_display_on_column_graphs():
    div_id = "test_id"
    result = display_on_column_graphs(div_id)
    assert div_id in result.id
    assert "column" in result.style["flexDirection"]


def test_get_input_elements():
    result = get_input_elements()
    assert len(result.children) == 2
    assert isinstance(result.children[0].children[0], dcc.Dropdown)
    assert isinstance(result.children[0].children[1], dcc.DatePickerRange)
    assert isinstance(result.children[1].children[0], html.Label)
    assert isinstance(result.children[1].children[1], dcc.Input)


def test_get_graphs_container():
    result = get_graphs_container()
    assert len(result.children) == 3
    assert result.children[0].id == "transition_column"
    assert result.children[1].id == "seasonal_column"
    assert result.children[2].id == "autocorelation_column"
