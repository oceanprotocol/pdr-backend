from typing import List, Optional

import dash_bootstrap_components as dbc
from dash import html
from pdr_backend.cli.arg_feeds import ArgFeed
from pdr_backend.pdr_dashboard.dash_components.plots import (
    get_feed_figures,
    get_predictoor_figures,
)
from pdr_backend.pdr_dashboard.dash_components.view_elements import get_graph


def get_modal(
    modal_id: str,
):
    return dbc.Modal(
        ModalContent(modal_id).get_content(),
        id=modal_id,
    )


class ModalContent:
    def __init__(
        self,
        modal_id: str,
        data_manager=None,
    ):
        self.modal_id = modal_id
        self.data_manager = data_manager

        self.selected_row: Optional[dict] = None
        self.figures: List = []

    def get_content(self) -> List:
        self.create_figures()

        return [self.get_header(), self.get_body()]

    def get_header(self) -> html.Div:
        modal_header_title = "Loading data"

        if self.selected_row:
            if self.modal_id == "predictoors_modal":
                modal_header_title = f"{self.selected_row['addr']} - Predictoor Data"
            elif self.modal_id == "feeds_modal":
                sr = self.selected_row
                modal_header_title = f"""{sr["base_token"]}-{sr["quote_token"]}
                {sr["timeframe"]} {sr["source"]}
                """

        header = html.Div(
            html.Span(
                modal_header_title,
                className="modal-graph-title",
            ),
            id=f"{self.modal_id}-header",
            className="modal-graph-header",
        )

        return header

    def get_body(self) -> html.Div:
        graphs = [
            html.Div(get_graph(fig), className="modal-graph-item")
            for fig in self.figures
        ]

        body = html.Div(
            graphs,
            id=f"{self.modal_id}-body",
            className="modal-graph-body",
        )

        return body

    def create_figures(self):
        selected_row = self.selected_row
        figures_func = (
            get_predictoor_figures
            if self.modal_id == "predictoors_modal"
            else get_feed_figures
        )

        if not selected_row:
            figures_args: List[List] = (
                [[], []] if self.modal_id == "feeds_modal" else [[]]
            )
            self.figures = figures_func(*figures_args).get_figures()
            return

        if self.modal_id == "feeds_modal":
            feed = ArgFeed(
                exchange=selected_row["source"].lower(),
                signal=None,
                pair=f'{selected_row["base_token"]}-{selected_row["quote_token"]}',
                timeframe=selected_row["timeframe"],
                contract=selected_row["full_addr"],
            )

            payouts = self.data_manager.payouts(
                [feed.contract], None, self.data_manager.start_date
            )
            subscriptions = self.data_manager.feed_daily_subscriptions_by_feed_id(
                feed.contract
            )
            figures_args = [payouts, subscriptions]
        elif self.modal_id == "predictoors_modal":
            payouts = self.data_manager.payouts(
                feed_addrs=[],
                predictoor_addrs=[selected_row["full_addr"]],
                start_date=self.data_manager.start_date,
            )
            figures_args = [payouts]

        self.figures = figures_func(*figures_args).get_figures()
