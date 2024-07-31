import dash_bootstrap_components as dbc
from dash import dash_table, dcc, html
from typing import List, Dict, Any, Union, Tuple


NAV_ITEMS = [{"text": "Home", "location": "/"}, {"text": "Feeds", "location": "/feeds"}]


def col_to_human(col):
    col = col.replace("avg_", "")
    col = col.replace("total_", "")

    return col.replace("_", " ").title()


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
        case _:
            return ""


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


def get_feeds_switch():
    return html.Div(
        [
            dbc.Switch(
                id="toggle-switch-predictoor-feeds",
                label="Predictoor feeds only",
                value=True,
            ),
            get_tooltip_and_button("switch-feeds"),
        ],
        style={"display": "flex"},
    )


def get_predictoors_switch(selected_items):
    return html.Div(
        [
            dbc.Switch(
                id="show-favourite-addresses",
                label="Select configured predictoors",
                value=bool(selected_items),
            ),
            get_tooltip_and_button("switch-predictoors"),
        ],
        style={"display": "flex"},
    )


def get_feeds_data(app):
    data = app.feeds_data

    columns = [{"name": col_to_human(col), "id": col} for col in data[0].keys()]
    hidden_columns = ["contract"]

    return (columns, hidden_columns), data

def get_feeds_stat_with_contract(
        contract: str,
        feed_stats: List[Dict[str, Any]]
) -> Union[Tuple[float, float, float], None]:
    for feed in feed_stats:
        if feed["contract"] == contract:
            return (
                round(feed["avg_accuracy"],2),
                round(feed["volume"], 2),
                round(feed["avg_stake"], 2)
            )
        
    return None

def get_feeds_data_for_feeds_table(app, feed_stats: List[Dict[str, Any]]):
    temp_data = app.feeds_data

    new_feed_data = []
    ## split the pair column into two columns
    for feed in temp_data:
        split_pair = feed["pair"].split("/")
        feed_item = {}
        feed_item["addr"] = feed["contract"][:5] + "..." + feed["contract"][-5:]
        feed_item["base_token"] = split_pair[0]
        feed_item["quote_token"] = split_pair[1]
        feed_item["exchange"] = feed["source"].capitalize()
        feed_item["time"] = feed["timeframe"]

        result = get_feeds_stat_with_contract(feed["contract"], feed_stats)
        if result:
            feed_item["avg_accuracy"] = result[0]
            feed_item["avg_stake"] = result[2]
            feed_item["volume"] = result[1]

        new_feed_data.append(feed_item)

    columns = [
        {"name": col_to_human(col), "id":col} for col in new_feed_data[0].keys()
    ]

    return columns, new_feed_data

def get_predictoors_data(app):
    columns = [
        {"name": col_to_human(col), "id": col} for col in app.predictoors_data[0].keys()
    ]
    hidden_columns = ["user"]

    if app.favourite_addresses:
        data = [
            p for p in app.predictoors_data if p["user"] in app.favourite_addresses
        ] + [
            p for p in app.predictoors_data if p["user"] not in app.favourite_addresses
        ]
    else:
        data = app.predictoors_data

    return (columns, hidden_columns), data


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


def get_table(
    table_id,
    table_name,
    searchable_field,
    columns,
    data,
    selected_items=None,
    length=0,
):
    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Span(
                                table_name, style={"fontSize": "20px", "height": "100%"}
                            ),
                            html.Span(
                                id=f"table-rows-count-{table_id}",
                                children=f"({length})",
                                style={
                                    "fontSize": "16px",
                                    "color": "gray",
                                    "hight": "100%",
                                    "marginLeft": "4px",
                                },
                            ),
                        ],
                        style={
                            "display": "flex",
                            "justifyContet": "center",
                            "alignItems": "center",
                        },
                    ),
                    (
                        get_feeds_switch()
                        if table_name == "Feeds"
                        else get_predictoors_switch(selected_items=selected_items)
                    ),
                ],
                className="table-title",
            ),
            html.Div(
                [
                    dcc.Input(
                        id=f"search-input-{table_name}",
                        type="text",
                        placeholder=f"Search for {searchable_field}",
                        debounce=True,  # Trigger the input event after user stops typing
                        style={"fontSize": "15px", "min-width": "100px"},
                    ),
                    html.Div(
                        [
                            html.Button(
                                "Select All",
                                id=f"select-all-{table_id}",
                                n_clicks=0,
                                className="button-select-all",
                            ),
                            html.Button(
                                "Clear",
                                id=f"clear-all-{table_id}",
                                n_clicks=0,
                                className="button-clear-all",
                            ),
                        ],
                        className="wrap-with-gap",
                    ),
                ],
                className="wrap-with-gap",
            ),
            dash_table.DataTable(
                id=table_id,
                columns=columns[0],
                hidden_columns=columns[1],
                data=data,
                row_selectable="multi",  # Can be 'multi' for multiple rows
                selected_rows=selected_items if selected_items else [],
                sort_action="native",  # Enables data to be sorted
                style_cell={"textAlign": "left"},
                style_table={
                    "height": "30vh",
                    "width": "100%",
                    "overflow": "auto",
                    "paddingTop": "5px",
                },
                fill_width=True,
            ),
        ],
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

def get_feeds_table_area(
    columns,
    feeds_data,
):
    return html.Div(
        [
            dash_table.DataTable(
                id='feeds_table',
                columns=columns,
                data=feeds_data,
                style_table={'overflowX': 'auto'},
                sort_action="native",    # Enables sorting feature
            )
        ],
        style={"width": "100%"}
    )
