import dash
from dash import Input, Output, State, html

from pdr_backend.pdr_dashboard.dash_components.modal import ModalContent
from pdr_backend.pdr_dashboard.pages.predictoors import get_metric, key_id_name
from pdr_backend.pdr_dashboard.util.filters import (
    check_conditions,
    filter_table_by_range,
)
from pdr_backend.pdr_dashboard.util.format import format_df
from pdr_backend.pdr_dashboard.util.helpers import (
    toggle_modal_helper,
)


def get_callbacks_predictoors(app):
    @app.callback(
        Output("predictoors_page_table", "data", allow_duplicate=True),
        Output("predictoors_page_metrics_row", "children"),
        Output("predictoors_page_table_control", "children"),
        [Input("start-date", "data")],
        prevent_initial_call=True,
    )
    def update_page_data(_start_date):
        app.data.refresh_predictoors_data()
        stats = app.data.predictoors_metrics()

        metrics_children_data = [
            get_metric(
                label=key,
                value=value,
                value_id=key_id_name(key),
            )
            for key, value in stats.items()
        ]

        return (
            app.data.predictoors_table_data.to_dicts(),
            metrics_children_data,
            html.Div(),
        )

    @app.callback(
        Output("predictoors_page_table", "data"),
        [
            Input("apr_button", "n_clicks"),
            Input("p_avg_accuracy_button", "n_clicks"),
            Input("gross_income_button", "n_clicks"),
            Input("nr_feeds_button", "n_clicks"),
            Input("staked_button", "n_clicks"),
            Input("tx_costs_button", "n_clicks"),
            Input("stake_loss_button", "n_clicks"),
            Input("net_income_button", "n_clicks"),
            Input("search-input-predictoors-table", "value"),
            Input("predictoors_page_table", "sort_by"),
        ],
        State("apr_min", "value"),
        State("apr_max", "value"),
        State("p_avg_accuracy_min", "value"),
        State("p_avg_accuracy_max", "value"),
        State("gross_income_min", "value"),
        State("gross_income_max", "value"),
        State("nr_feeds_min", "value"),
        State("nr_feeds_max", "value"),
        State("staked_min", "value"),
        State("staked_max", "value"),
        State("tx_costs_min", "value"),
        State("tx_costs_max", "value"),
        State("stake_loss_min", "value"),
        State("stake_loss_max", "value"),
        State("net_income_min", "value"),
        State("net_income_max", "value"),
        prevent_initial_call=True,
    )
    # pylint: disable=too-many-positional-arguments
    def filter_table(
        _n_clicks_apr,
        _n_clicks_p_avg_accuracy,
        _n_clicks_gross_income,
        _n_clicks_nr_feeds,
        _n_clicks_staked,
        _n_clicks_tx_costs,
        _n_clicks_stake_loss,
        _n_clicks_net_income,
        search_input_value,
        sort_by,
        apr_min,
        apr_max,
        p_avg_accuracy_min,
        p_avg_accuracy_max,
        gross_income_min,
        gross_income_max,
        nr_feeds_min,
        nr_feeds_max,
        staked_min,
        staked_max,
        tx_costs_min,
        tx_costs_max,
        stake_loss_min,
        stake_loss_max,
        net_income_min,
        net_income_max,
    ):
        """
        Filter table based on selected dropdown values.
        """

        conditions = [
            ("range", "apr", apr_min, apr_max),
            ("range", "p_avg_accuracy", p_avg_accuracy_min, p_avg_accuracy_max),
            ("range", "gross_income", gross_income_min, gross_income_max),
            ("range", "feed_count", nr_feeds_min, nr_feeds_max),
            ("range", "total_stake", staked_min, staked_max),
            ("range", "tx_costs_(OCEAN)", tx_costs_min, tx_costs_max),
            ("range", "stake_loss", stake_loss_min, stake_loss_max),
            ("range", "net_income_(OCEAN)", net_income_min, net_income_max),
            ("search", None, search_input_value),
        ]

        new_table_data = check_conditions(app.data.raw_predictoors_data, conditions)

        if sort_by:
            # Extract sort criteria
            sort_col = sort_by[0]["column_id"]
            descending = sort_by[0]["direction"] == "desc"
            new_table_data = new_table_data.sort(
                by=[sort_col, "full_addr"], descending=descending
            )

        return format_df(new_table_data).to_dicts()

    @app.callback(
        Output("apr_dropdown", "label"),
        State("apr_min", "value"),
        State("apr_max", "value"),
        Input("apr_button", "n_clicks"),
        Input("clear_predictoors_filters_button", "n_clicks"),
    )
    def filter_table_by_apr_range(
        min_val, max_val, _n_clicks_apr_btn, _n_clicks_filters_bnt
    ):
        return filter_table_by_range(min_val, max_val, "APR")

    @app.callback(
        Output("p_avg_accuracy_dropdown", "label"),
        State("p_avg_accuracy_min", "value"),
        State("p_avg_accuracy_max", "value"),
        Input("p_avg_accuracy_button", "n_clicks"),
        Input("clear_predictoors_filters_button", "n_clicks"),
    )
    def filter_table_by_p_avg_accuracy_range(
        min_val, max_val, _n_clicks_p_avg_accuracy_btn, _n_clicks_filters_bnt
    ):
        return filter_table_by_range(min_val, max_val, "Accuracy")

    @app.callback(
        Output("gross_income_dropdown", "label"),
        State("gross_income_min", "value"),
        State("gross_income_max", "value"),
        Input("gross_income_button", "n_clicks"),
        Input("clear_predictoors_filters_button", "n_clicks"),
    )
    def filter_table_by_gross_income_range(
        min_val, max_val, _n_clicks_gross_income_btn, _n_clicks_filters_bnt
    ):
        return filter_table_by_range(min_val, max_val, "Gross Income")

    @app.callback(
        Output("nr_feeds_dropdown", "label"),
        State("nr_feeds_min", "value"),
        State("nr_feeds_max", "value"),
        Input("nr_feeds_button", "n_clicks"),
        Input("clear_predictoors_filters_button", "n_clicks"),
    )
    def filter_table_by_nr_feeds_range(
        min_val, max_val, _n_clicks_nr_feeds_btn, _n_clicks_filters_bnt
    ):
        return filter_table_by_range(min_val, max_val, "Nr Feeds")

    @app.callback(
        Output("staked_dropdown", "label"),
        State("staked_min", "value"),
        State("staked_max", "value"),
        Input("staked_button", "n_clicks"),
        Input("clear_predictoors_filters_button", "n_clicks"),
    )
    def filter_table_by_stake_range(
        min_val, max_val, _n_clicks_stake_btn, _n_clicks_filters_bnt
    ):
        return filter_table_by_range(min_val, max_val, "Staked")

    @app.callback(
        Output("tx_costs_dropdown", "label"),
        State("tx_costs_min", "value"),
        State("tx_costs_max", "value"),
        Input("tx_costs_button", "n_clicks"),
        Input("clear_predictoors_filters_button", "n_clicks"),
    )
    def filter_table_by_costs_range(
        min_val, max_val, _n_clicks_tx_costs_btn, _n_clicks_filters_bnt
    ):
        return filter_table_by_range(min_val, max_val, "Tx Costs")

    @app.callback(
        Output("stake_loss_dropdown", "label"),
        State("stake_loss_min", "value"),
        State("stake_loss_max", "value"),
        Input("stake_loss_button", "n_clicks"),
        Input("clear_predictoors_filters_button", "n_clicks"),
    )
    def filter_table_by_stake_loss_range(
        min_val, max_val, _n_clicks_stake_loss_btn, _n_clicks_filters_bnt
    ):
        return filter_table_by_range(min_val, max_val, "Stake Loss")

    @app.callback(
        Output("net_income_dropdown", "label"),
        State("net_income_min", "value"),
        State("net_income_max", "value"),
        Input("net_income_button", "n_clicks"),
        Input("clear_predictoors_filters_button", "n_clicks"),
    )
    def filter_table_by_net_income_range(
        min_val, max_val, _n_clicks_net_income_btn, _n_clicks_filters_bnt
    ):
        return filter_table_by_range(min_val, max_val, "Net Income")

    @app.callback(
        Output("apr_min", "value"),
        Output("apr_max", "value"),
        Output("p_avg_accuracy_min", "value"),
        Output("p_avg_accuracy_max", "value"),
        Output("gross_income_min", "value"),
        Output("gross_income_max", "value"),
        Output("nr_feeds_min", "value"),
        Output("nr_feeds_max", "value"),
        Output("staked_min", "value"),
        Output("staked_max", "value"),
        Output("tx_costs_min", "value"),
        Output("tx_costs_max", "value"),
        Output("stake_loss_min", "value"),
        Output("stake_loss_max", "value"),
        Output("net_income_min", "value"),
        Output("net_income_max", "value"),
        Output("search-input-predictoors-table", "value"),
        Input("clear_predictoors_filters_button", "n_clicks"),
    )
    def clear_all_filters(btn_clicks):
        if not btn_clicks:
            return dash.no_update

        return (
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            "",
        )

    @app.callback(
        Output("predictoors_modal", "is_open"),
        Output("predictoors_page_table", "selected_rows"),
        [
            Input("predictoors_page_table", "selected_rows"),
            Input("predictoors_modal", "is_open"),
        ],
    )
    def toggle_modal(selected_rows, is_open_input):
        ctx = dash.callback_context
        return toggle_modal_helper(
            ctx,
            "predictoors_modal",
            bool(is_open_input),
            selected_rows,
        )

    @app.callback(
        Output("predictoors_modal", "children"),
        Input("predictoors_modal", "is_open"),
        State("predictoors_page_table", "selected_rows"),
        State("predictoors_page_table", "data"),
    )
    # pylint: disable=unused-argument
    def update_graphs(is_open, selected_rows, predictoors_table_data):
        content = ModalContent("predictoors_modal", app.data)
        content.selected_row = (
            predictoors_table_data[selected_rows[0]] if selected_rows else None
        )

        return content.get_content()
