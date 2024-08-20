from typing import Optional

import dash_bootstrap_components as dbc
from dash import dcc, html


class Filter:
    def __init__(self, name, placeholder, options):
        self.name = name
        self.placeholder = placeholder
        self.options = options


class TabularPage:
    def get_multiselect_dropdown(self, filter_obj: Filter):
        return dcc.Dropdown(
            id=filter_obj.name,
            options=filter_obj.options,
            multi=True,
            value=[],
            placeholder=filter_obj.placeholder,
            style={"width": "140px", "borderColor": "#aaa"},
        )

    def get_input_filter(self, label: str, page: Optional[str] = None):
        return dbc.DropdownMenu(
            [
                self.get_input_with_label("Min", label, page=page),
                self.get_input_with_label("Max", label, page=page),
                html.Button(
                    "Apply Filter",
                    className="btn-apply-filter",
                    id=f"{button_label(label, page)}_button",
                ),
            ],
            id=f"{button_label(label, page)}_dropdown",
            label=label,
            style={
                "backgroundColor": "white",
            },
            toggleClassName="dropdown-toggle-container",
        )

    def get_input_with_label(self, label: str, name: str, page: Optional[str] = None):
        return html.Div(
            [
                html.Label(label),
                dcc.Input(id=f"{button_label(name, page)}_{button_label(label, page)}"),
            ],
            className="input-with-label",
        )


def add_to_filter(filter_options, value):
    if value not in filter_options:
        filter_options.append(value)


def button_label(label, page):
    if label == "Accuracy" and page == "predictoors":
        return "p_accuracy"

    label = label.replace(" ", "_")

    return label.lower()
