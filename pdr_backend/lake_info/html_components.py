import dash_bootstrap_components as dbc
from dash import html

from pdr_backend.util.time_types import UnixTimeMs


def get_types_table(df):
    types = []
    for col in df.iter_columns():
        types.append(html.Tr([html.Td(str(col.name)), html.Td(str(col.dtype))]))

    types_table = dbc.Table(types, bordered=True)

    return html.Div(
        [html.Strong("Schema"), types_table],
    )


def fallback_badge(text, value):
    nat_str = (
        UnixTimeMs(value).to_timestr() if isinstance(value, (int, float)) else None
    )

    return dbc.Button(
        [
            text,
            dbc.Badge(
                str(value) if value is not None else "no data",
                color="light",
                text_color="primary" if value is not None else "danger",
                className="ms-1",
            ),
            " aka ",
            dbc.Badge(
                str(nat_str),
                color="light",
                text_color="primary" if value is not None else "danger",
                className="ms-1",
            ),
        ],
        color="primary" if value else "danger",
        style={"margin-bottom": "10px"},
    )


def simple_badge(text, value):
    return dbc.Button(
        [
            text,
            dbc.Badge(
                str(value),
                color="light",
                text_color="primary",
                className="ms-1",
            ),
        ],
        color="primary",
    )


def alert_validation_error(violation: str):
    return dbc.Alert(
        [html.I(className="bi bi-x-octagon-fill me-2"), violation],
        color="danger",
        className="d-flex align-items-center",
    )


def get_overview_summary(dfs):
    rows = [
        html.Tr(
            [
                html.Th("Table name"),
                html.Th("Number of rows"),
                html.Th("Min timestamp"),
                html.Th("Max timestamp"),
                html.Th("Min datestr"),
                html.Th("Max datestr"),
            ]
        )
    ]

    for name, df in dfs.items():
        cells = [
            name,
            df.shape[0],
            df["timestamp"].min() if "timestamp" in df.columns else "-",
            df["timestamp"].max() if "timestamp" in df.columns else "-",
            (
                UnixTimeMs(df["timestamp"].min()).to_timestr()
                if "timestamp" in df.columns
                else "-"
            ),
            (
                UnixTimeMs(df["timestamp"].max()).to_timestr()
                if "timestamp" in df.columns
                else "-"
            ),
        ]

        rows.append(html.Tr([html.Td(cell) for cell in cells]))

    return dbc.Table(rows, bordered=True, striped=True, hover=True, responsive=True)
