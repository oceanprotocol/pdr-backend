from typing import List

import dash_bootstrap_components as dbc
from dash import html
from pdr_backend.pdr_dashboard.dash_components.view_elements import get_graph


def get_modal(
    modal_id: str,
):
    return dbc.Modal(
        get_default_modal_content(modal_id),
        id=modal_id,
    )


def get_default_modal_content(modal_id: str, figures: List = []):
    return [
        dbc.ModalHeader("Loading data", id=f"{modal_id}-header"),
        get_graphs_modal_body(figures, modal_id),
    ]


def get_graphs_modal_header(modal_header_title: str, modal_id: str):
    return html.Div(
        html.Span(
            modal_header_title,
            className="modal-graph-title",
        ),
        id=f"{modal_id}-header",
        className="modal-graph-header",
    )


def get_graphs_modal_body(figures: List, modal_id: str):
    return html.Div(
        [html.Div(get_graph(fig), className="modal-graph-item") for fig in figures],
        id=f"{modal_id}-body",
        className="modal-graph-body",
    )
