import os
from pathlib import Path

import dash_bootstrap_components as dbc
import yaml
from dash import dcc, html

from pdr_backend.pdr_dashboard.util.format import format_value

NAV_ITEMS = [
    {"text": "Home", "location": "/"},
    {"text": "Feeds", "location": "/feeds"},
    {"text": "Predictoors", "location": "/predictoors"},
]


# pylint: disable=too-many-return-statements
def get_information_text(tooltip_id: str):
    fiile = os.path.join(Path(__file__).parent, "tooltips.yaml")

    try:
        with open(fiile, "r") as file:
            tooltips = yaml.safe_load(file.read())
    except FileNotFoundError:
        return ""

    return tooltips.get(tooltip_id, "")


def get_period_selection_radio_items(component_id: str):
    return dcc.RadioItems(
        className="date-period-radio-items",
        id=f"{component_id}-date-period-radio-items",
        options=[
            {"label": "1D", "value": "1"},
            {"label": "1W", "value": "7"},
            {"label": "1M", "value": "30"},
            {"label": "ALL", "value": "0"},
        ],
        value="30",  # default selected value
        labelStyle={"display": "inline-block", "margin-right": "10px"},
    )


def get_tooltip_and_button(value_id: str):
    return html.Span(
        [
            dbc.Button(
                "?", id=f"tooltip-target-{value_id}", className="tooltip-question-mark"
            ),
            dbc.Tooltip(
                get_information_text(f"tooltip-{value_id}"),
                target=f"tooltip-target-{value_id}",
                placement="right",
            ),
        ]
    )


def get_metric(label, value, value_id):
    return html.Div(
        [
            html.Span(
                [
                    label,
                    get_tooltip_and_button(value_id),
                ],
                style={
                    "display": "flex",
                    "justifyContent": "center",
                    "alignItems": "center",
                },
            ),
            html.Span(
                id=value_id,
                children=html.Div(className="initial_metric"),
                className="metric_value",
            ),
        ],
        className="metric_unit",
    )


def get_layout():
    return html.Div(
        [
            dcc.Location(id="url", refresh=False),
            dcc.Store(id="is-initial-data-loaded"),
            dcc.Store(id="start-date"),
            get_header(),
            html.Div(id="page-content"),
        ]
    )


def get_graph(figure):
    return dcc.Graph(figure=figure, style={"width": "100%", "height": "25vh"})


def get_header():
    return html.Div(
        [html.Div(id="navbar-container"), get_available_data_area_components()],
        className="header-container",
        style={
            "display": "flex",
            "justifyContent": "space-between",
            "alignItems": "center",
        },
    )


def get_navbar(nav_items):
    return dbc.NavbarSimple(
        children=[
            get_nav_item(item["text"], item["location"], item.get("active", False))
            for item in nav_items
        ],
        brand_href="/",
        color="transparent",
        style={
            "display": "flex",
            "justifyContent": "flexStart",
            "alignItems": "center",
            "backgroundColor": "transparent",
        },
    )


def get_nav_item(text: str, location: str, active: bool):
    return dbc.NavItem(
        dbc.NavLink(
            text,
            id=text.lower(),
            href=location,
            active=active,
        )
    )


def get_search_bar(component_id, placeholder):
    return (
        dcc.Input(
            id=component_id,
            className="search-input",
            type="text",
            placeholder=placeholder,
        ),
    )


def get_available_period_text_display():
    return html.Div(
        [
            html.Span(
                "available lake data",
                style={"lineHeight": "1", "fontSize": "16px", "marginBottom": "4px"},
            ),
            html.Span(id="available-data-text", style={"lineHeight": "1"}),
        ],
        style={
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "center",
        },
    )


def get_available_data_area_components():
    return html.Div(
        [
            get_available_period_text_display(),
            get_period_selection_radio_items("general-lake"),
        ],
        style={"display": "flex", "justifyContent": "center", "alignItems": "center"},
    )


def div_with_loading(div_id: str, style=None):
    return dcc.Loading(
        id=f"loading_{div_id}",
        type="default",
        children=html.Div(id=div_id, style=style),
        custom_spinner=html.H2(dbc.Spinner(), style={"height": "100%"}),
    )


def table_initial_spinner():
    return html.Div(id="table_spinner")
