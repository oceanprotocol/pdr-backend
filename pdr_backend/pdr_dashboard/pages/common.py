from dash import dcc, html
import dash_bootstrap_components as dbc


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

    def get_input_filter(self, label: str):
        return dbc.DropdownMenu(
            [
                self.get_input_with_label("Min", label),
                self.get_input_with_label("Max", label),
                html.Button(
                    "Apply Filter",
                    className="btn-apply-filter",
                    id=f"{label.lower()}_button",
                ),
            ],
            id=f"{label.lower()}_dropdown",
            label=label,
            style={
                "backgroundColor": "white",
            },
            toggleClassName="dropdown-toggle-container",
        )

    def get_input_with_label(self, label: str, name: str):
        return html.Div(
            [html.Label(label), dcc.Input(id=f"{name.lower()}_{label.lower()}")],
            className="input-with-label",
        )


def add_to_filter(filter_options, value):
    if value not in filter_options:
        filter_options.append(value)
