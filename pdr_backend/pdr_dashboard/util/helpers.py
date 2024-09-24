from functools import wraps

import dash
from dash import dcc, html
import dash_bootstrap_components as dbc


def toggle_modal_helper(
    ctx,
    selected_rows,
    is_open_input,
    modal_id=None,
):
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


def wrap_outputs(results, loading_id_prefix="loading", spinner=None):
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
            children=html.Span(results[i]),
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
            return wrap_outputs(results, loading_id_prefix, spinner)

        return wrapper

    return decorator
