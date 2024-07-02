import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table
import pandas as pd
import plotly.graph_objects as go

def get_input_column():
    return html.Div(
        [
            html.Div(id="feeds_container", style={"height": "50%"}),
            html.Div(id="predictoors_container", style={"height": "50%"}),
        ],
        style={
            "height": "100%",
            "display": "flex",
            "flex": 1,
            "flexDirection": "column",
            "justifyContent": "space-around",
        },
    )


def get_graphs_column():
    return html.Div(
        [
            html.Div(id="predictoors_stake_container", style={"height": "50px", "backgroundColor": "black"}),
            html.Div(id="graph2_container", style={"height": "50px", "backgroundColor": "blue"}),
        ],
        id="graphs_container",
        style={
            "height": "100%",
            "display": "flex",
            "flex": 3,
            "flexDirection": "column",
            "justifyContent": "space-around",
        }
    )

def get_predictoors_stake_graph(predictoors_stake_data):

    df = pd.DataFrame(predictoors_stake_data)

    fig = go.Figure()

    users = df['user'].unique()
    for user in users:
        user_data = df[df['user'] == user]
        fig.add_trace(go.Bar(
            x=user_data['slot'],
            y=user_data['stake'],
            name=user
        ))

    fig.update_layout(
        barmode='stack',
        title='Bar Chart with Long Format Data',
        bargap=0,
    )

    return dcc.Graph(figure=fig, id="predictoors_stake_graph")
    

def get_layout():
    return html.Div(
        [
            dcc.Store(id="data-folder"),
            dcc.Store(id="feeds-data"),
            dcc.Store(id="predictoors-data"),
            dcc.Store(id="predictoors-stake-data"),
            html.H1(
                "Predictoor dashboard",
                id="page_title",
                style={"width": "100%", "textAlign": "center"},
            ),
            html.Div(id="error-message"),
            dcc.Loading(
                id="loading",
                type="default",
                children=[
                    html.Div(
                        id="feeds_container", 
                        style={
                                "display": "flex",
                                "flexDirection": "row",
                            },
                        children=[get_input_column(), get_graphs_column()],
                    )
                ],
                style={
                    "height": "100%",
                    "width": "100%",
                    "display": "flex",
                    "alignItems": "flexStart",
                },
                custom_spinner=html.H2(dbc.Spinner(), style={"height": "100%"}),
            ),
        ],
    )


def get_table(table_id, table_name, columns, data):
    return html.Div(
        [
            html.H3(table_name),
            dash_table.DataTable(
                id=table_id,
                columns=[{"name": col, "id": col} for col in columns],
                data=data,
                row_selectable="multi",  # Can be 'multi' for multiple rows
                selected_rows=[],
                style_cell={"textAlign": "left"},
                style_table={
                    "height": "35vh",
                    "width": "100%",
                    "overflow": "auto",
                    "marginTop": "5px",
                },
                fill_width=True,
            ),
        ],
        style={"marginBottom": "40px"},
    )
