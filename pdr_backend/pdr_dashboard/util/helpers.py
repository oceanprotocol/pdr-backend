from functools import wraps
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import dash
import polars as pl
from enforce_typing import enforce_types

import dash_bootstrap_components as dbc
from dash import dcc, html

from pdr_backend.util.time_types import UnixTimeS
from pdr_backend.pdr_dashboard.pages.common import Filter


@enforce_types
def toggle_modal_helper(
    ctx: dash._callback_context.CallbackContext,
    modal_id: str,
    is_open_input: bool,
    selected_rows: Optional[List],
) -> Tuple[bool, List[int]]:
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    modal_type = modal_id.split("_")[0]
    safe_trigger_ids = [f"{modal_type}_page_table", modal_id]

    if triggered_id not in safe_trigger_ids:
        return dash.no_update, dash.no_update

    if triggered_id == modal_id:
        if is_open_input:
            return dash.no_update, dash.no_update

        # Modal close button is clicked, clear the selection
        return False, []

    if selected_rows and not is_open_input:
        return True, dash.no_update

    # Clear the selection if modal is not opened
    return False, []


def wrap_outputs_loading(results, loading_id_prefix="loading", spinner=None):
    """
    Wraps the callback results in a `dcc.Loading` component with `dbc.Spinner`.

    Args:
        results (tuple or any): The callback results that need to be wrapped.
        loading_id_prefix (str): The prefix for the loading component IDs.
        spinner: Optional custom spinner from `dash_bootstrap_components.Spinner`.

    Returns:
        tuple: Wrapped outputs in `dcc.Loading` components.
    """
    if not isinstance(results, tuple):
        results = (results,)

    # Wrap each output in a `dcc.Loading` component
    wrapped_outputs = [
        dcc.Loading(
            id=f"{loading_id_prefix}_{i}",
            type="default",
            children=results[i],
            custom_spinner=spinner or html.H2(dbc.Spinner(), style={"height": "100%"}),
        )
        for i in range(len(results))
    ]

    return tuple(wrapped_outputs)


def with_loading(loading_id_prefix="loading", spinner=None):
    """
    A decorator that wraps the outputs of a Dash callback with `dcc.Loading`.

    Args:
        loading_id_prefix (str): Prefix for the loading component IDs.
        spinner: Optional custom spinner.

    Returns:
        function: Decorated function with `dcc.Loading` wrapping the outputs.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            results = func(*args, **kwargs)
            return wrap_outputs_loading(results, loading_id_prefix, spinner)

        return wrapper

    return decorator


@enforce_types
def select_or_clear_all_by_table(
    ctx,
    table_id: str,
    rows: List[Dict[str, Any]],
) -> Union[List[int], dash.no_update]:
    """
    Select or unselect all rows in a table.
    Args:
        ctx (dash.callback_context): Dash callback context.
    Returns:
        list: List of selected rows or dash.no_update.
    """
    if not ctx.triggered:
        return dash.no_update

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    selected_rows = []
    if button_id == f"select-all-{table_id}":
        selected_rows = list(range(len(rows)))

    return selected_rows


@enforce_types
def _format_date_text(
    start_date: Optional[datetime], end_date: Optional[datetime]
) -> str:
    if not start_date or not end_date:
        return "there is no data available"

    return f"{start_date.strftime('%d-%m-%y')} -> {end_date.strftime('%d-%m-%y')}"


@enforce_types
def get_date_period_text_for_selected_predictoors(payouts: pl.DataFrame) -> str:
    if payouts.is_empty():
        return _format_date_text(None, None)

    start_date = UnixTimeS(payouts.item(0, "slot")).to_dt()
    end_date = UnixTimeS(payouts.item(-1, "slot")).to_dt()

    return _format_date_text(start_date, end_date)


@enforce_types
def get_date_period_text_header(start_date: UnixTimeS, end_date: UnixTimeS) -> str:
    return _format_date_text(start_date.to_dt(), end_date.to_dt())


def get_empty_feeds_filters() -> List[Filter]:
    filters = [
        {"name": "base_token", "placeholder": "Base Token", "options": []},
        {"name": "quote_token", "placeholder": "Quote Token", "options": []},
        {"name": "source", "placeholder": "Source", "options": []},
        {"name": "timeframe", "placeholder": "Timeframe", "options": []},
    ]

    return [Filter(**item) for item in filters]


@enforce_types
def produce_feeds_filter_options(
    df: pl.DataFrame,
) -> Tuple[List[str], List[str], List[str], List[str]]:
    df = df.with_columns(
        pl.col("pair")
        .str.split_exact("/", 1)
        .map_elements(lambda x: x["field_0"], return_dtype=pl.String)
        .alias("base_token"),
        pl.col("pair")
        .str.split_exact("/", 1)
        .map_elements(lambda x: x["field_1"], return_dtype=pl.String)
        .alias("quote_token"),
        pl.col("source").str.to_titlecase().alias("source"),
    )

    return (
        df["base_token"].unique().to_list(),
        df["quote_token"].unique().to_list(),
        df["source"].unique().to_list(),
        df["timeframe"].unique().to_list(),
    )


def check_data_loaded(
    output_count=1,
    alternative_output: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            is_initial_data_loaded = args[-1]  # assuming the last argument is the state
            if not is_initial_data_loaded or not is_initial_data_loaded["loaded"]:
                if alternative_output:
                    return alternative_output

                if output_count > 1:
                    return tuple(
                        dash.no_update for _ in range(output_count)
                    )  # multiple outputs

                return dash.no_update  # single output
            return func(*args, **kwargs)

        return wrapper

    return decorator


def get_feeds_for_favourite_predictoors(app, feed_data, predictoor_addrs):
    feed_ids = app.data.feed_ids_based_on_predictoors(predictoor_addrs)

    if not feed_ids:
        return [], feed_data

    feed_data = app.data.formatted_feeds_home_page_table_data.clone()
    feed_data = feed_data.filter(feed_data["contract"].is_in(feed_ids))

    return list(range(len(feed_ids))), feed_data
