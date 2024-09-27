from functools import wraps
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import dash
import polars as pl
from enforce_typing import enforce_types

import dash_bootstrap_components as dbc
from dash import dcc, html

from pdr_backend.util.time_types import UnixTimeS

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
