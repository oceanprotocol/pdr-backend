import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import dash
from enforce_typing import enforce_types

logger = logging.getLogger("predictoor_dashboard_utils")


# TODO: probably remove more functions from here, including this one
@enforce_types
def filter_objects_by_field(
    objects: List[Dict[str, Any]],
    field: str,
    search_string: str,
    previous_objects: Optional[List] = None,
) -> List[Dict[str, Any]]:
    if previous_objects is None:
        previous_objects = []

    return [
        obj
        for obj in objects
        if search_string.lower() in obj[field].lower() and obj not in previous_objects
    ]


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


def get_start_date_from_period(number_days: int):
    return int((datetime.now() - timedelta(days=number_days)).timestamp())


# TODO: use payouts as dataframe instead
def get_date_period_text_for_selected_predictoors(payouts: List):
    if payouts:
        return "there is no data available"
    start_date = payouts[0]["slot"] if len(payouts) > 0 else 0
    end_date = payouts[-1]["slot"] if len(payouts) > 0 else 0
    date_period_text = f"""
        {datetime.fromtimestamp(start_date).strftime('%d-%m-%y')}
        -> {datetime.fromtimestamp(end_date).strftime('%d-%m-%y')}
    """
    return date_period_text


def get_date_period_text_header(start_date: str, end_date: str):
    if not start_date or not end_date:
        return "there is no data available"
    date_period_text = f"""
        {datetime.fromtimestamp(float(start_date)).strftime('%d-%m-%y')}
        -> {datetime.fromtimestamp(float(end_date)).strftime('%d-%m-%y')}
    """
    return date_period_text


# TODO: remove
@enforce_types
def col_to_human(col: str, replace_rules: List[str] = ["avg_", "total_"]) -> str:
    temp_col = col
    for rule in replace_rules:
        temp_col = temp_col.replace(rule, "")

    return temp_col.replace("_", " ").title()


@enforce_types
def find_with_key_value(
    objects: List[Dict[str, Any]], key: str, value: str
) -> Union[Dict[str, Any], None]:
    for obj in objects:
        if obj[key] == value:
            return obj

    return None


def get_sales_str(result):
    sales_str = f"{result['sales']}"

    df_buy_count_str = (
        f"{result['df_buy_count']}-DF" if result["df_buy_count"] > 0 else ""
    )
    ws_buy_count_str = (
        f"{result['ws_buy_count']}-WS" if result["ws_buy_count"] > 0 else ""
    )

    if df_buy_count_str or ws_buy_count_str:
        counts_str = "_".join(filter(None, [df_buy_count_str, ws_buy_count_str]))

        if counts_str:
            sales_str += f"_{counts_str}"

    return sales_str
