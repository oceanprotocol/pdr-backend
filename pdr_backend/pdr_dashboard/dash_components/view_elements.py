import dash_bootstrap_components as dbc
from dash import dcc, html


NAV_ITEMS = [{"text": "Home", "location": "/"}, {"text": "Feeds", "location": "/feeds"}]


# pylint: disable=too-many-return-statements
def get_information_text(tooltip_id: str):
    match tooltip_id:
        case "tooltip-accuracy_metric":
            return """Average accuracy of predictions
                within the selected timeframe and for the selected predictoors and feeds."""
        case "tooltip-profit_metric":
            return """Total profit generated from predictions
                within the selected timeframe and for the selected predictoors and feeds."""
        case "tooltip-costs_metric":
            return """Transaction fee costs for predicting and claiming payouts
                for each slot individually within the selected timeframe
                and for the selected predictoors and feeds."""
        case "tooltip-stake_metric":
            return """Average stake placed on each prediction
                within the selected timeframe and for the selected predictoors and feeds."""
        case "tooltip-switch-predictoors":
            return """Toggle this switch to automatically select predictoors
                that are pre-configured in the ppss.yaml settings."""
        case "tooltip-switch-feeds":
            return """Toggle this switch to view only the feeds associated with
                the selected predictoors."""
        case "tooltip-feeds_page_Volume_metric":
            return "Total stake placed on predictions"
        case "tooltip-feeds_page_Feeds_metric":
            return "Total number of feeds"
        case "tooltip-feeds_page_Sales_metric":
            return "Number of subscriptions to feeds"
        case "tooltip-feeds_page_Revenue_metric":
            return "Total revenue generated from predictions"
        case "tooltip-feeds_page_Accuracy_metric":
            return "Average accuracy of predictions"

        case _:
            return ""


def get_date_period_selection_component():
    return html.Div(
        [
            dcc.RadioItems(
                id="date-period-radio-items",
                options=[
                    {"label": "1D", "value": "1"},
                    {"label": "1W", "value": "7"},
                    {"label": "1M", "value": "30"},
                    {"label": "ALL", "value": "0"},
                ],
                value="0",  # default selected value
                labelStyle={"display": "inline-block", "margin-right": "10px"},
            ),
            html.Span("there is no data available", id="available_data_period_text"),
        ]
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
            html.Span(value, id=value_id, style={"fontWeight": "bold"}),
        ],
        style={"display": "flex", "flexDirection": "column", "font-size": "20px"},
    )


def get_layout():
    return html.Div(
        [
            dcc.Location(id="url", refresh=False),
            html.Div(id="navbar-container"),
            html.Div(id="page-content"),
        ]
    )


def get_graph(figure):
    return dcc.Graph(figure=figure, style={"width": "100%", "height": "25vh"})


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
            "justifyContent": "center",
            "alignItems": "center",
            "backgroundColor": "transparent",
        },
    )


def get_nav_item(text: str, location: str, active: bool):
    return dbc.NavItem(
        dbc.NavLink(
            text,
            href=location,
            active=active,
            style={"fontSize": "26px", "margin": "0 10px"},
        )
    )
