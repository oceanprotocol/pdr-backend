import logging

from datetime import datetime, timedelta
from typing import Union, List, Dict, Any, Optional
from enforce_typing import enforce_types
import dash
from pdr_backend.pdr_dashboard.util.format import pick_from_dict, format_dict

logger = logging.getLogger("predictoor_dashboard_utils")


@enforce_types
def get_feed_column_ids(data: Dict[str, Any]):
    return [
        {"name": col_to_human(col=col, replace_rules=["total_"]), "id": col}
        for col in data.keys()
    ]


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


@enforce_types
def get_predictoors_data_from_payouts(
    user_payout_stats: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Process the user payouts stats data.
    Args:
        user_payout_stats (list): List of user payouts stats data.
    Returns:
        list: List of processed user payouts stats data.
    """

    for data in user_payout_stats:
        formatted_data = format_dict(
            pick_from_dict(
                data=data, keys=["user", "total_profit", "avg_accuracy", "avg_stake"]
            )
        )

        new_data = {
            "user_address": formatted_data["user"],
            "total_profit": formatted_data["total_profit"],
            "avg_accuracy": formatted_data["avg_accuracy"],
            "avg_stake": formatted_data["avg_stake"],
            "user": data["user"],
        }

        data.clear()
        data.update(new_data)

    return user_payout_stats


def get_start_date_from_period(number_days: int):
    return int((datetime.now() - timedelta(days=number_days)).timestamp())


def get_date_period_text(payouts: List):
    if not payouts:
        return "there is no data available"
    start_date = payouts[0]["slot"] if len(payouts) > 0 else 0
    end_date = payouts[-1]["slot"] if len(payouts) > 0 else 0
    date_period_text = f"""
        available {datetime.fromtimestamp(start_date).strftime('%d-%m-%Y')}
        - {datetime.fromtimestamp(end_date).strftime('%d-%m-%Y')}
    """
    return date_period_text


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
