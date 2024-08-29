import logging
from copy import deepcopy
from datetime import datetime, timedelta
from typing import Union, List, Dict, Any, Optional, Tuple
import dash
from enforce_typing import enforce_types
from pdr_backend.pdr_dashboard.util.format import (
    format_table,
    pick_from_dict,
    format_dict,
)

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
def get_predictoors_home_page_table_data(
    user_payout_stats: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Process the user payouts stats data.
    Args:
        user_payout_stats (list): List of user payouts stats data.
    Returns:
        list: List of processed user payouts stats data.
    """

    payout_stats = deepcopy(user_payout_stats)
    for data in payout_stats:
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

    return payout_stats


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


def get_feeds_stat_with_contract(
    contract: str, feed_stats: List[Dict[str, Any]]
) -> Dict[str, Union[float, int]]:
    result = find_with_key_value(feed_stats, "contract", contract)

    if result:
        return {
            "avg_accuracy": float(result["avg_accuracy"]),
            "avg_stake_per_epoch_(OCEAN)": float(result["avg_stake"]),
            "volume_(OCEAN)": float(result["volume"]),
        }

    return {
        "avg_accuracy": 0,
        "avg_stake_per_epoch_(OCEAN)": 0,
        "volume_(OCEAN)": 0,
    }


def get_feeds_subscription_stat_with_contract(
    contract: str, feed_subcription_stats: List[Dict[str, Any]]
) -> Dict[str, Union[float, int, str]]:
    result = find_with_key_value(feed_subcription_stats, "contract", contract)

    if result:
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

        return {
            "price_(OCEAN)": result["price"],
            "sales": sales_str,
            "sales_raw": result["sales"],
            "sales_revenue_(OCEAN)": result["sales_revenue"],
        }

    return {
        "price_(OCEAN)": 0,
        "sales": 0,
        "sales_raw": 0,
        "sales_revenue_(OCEAN)": 0,
    }


def get_feeds_data_for_feeds_table(
    feeds_data: List[Dict[str, Any]],
    feed_stats: List[Dict[str, Any]],
    feed_subcription_stats: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, str]], List[Dict[str, Any]], List[Dict[str, Any]]]:

    new_feed_data = []
    ## split the pair column into two columns
    for feed in feeds_data:
        split_pair = feed["pair"].split("/")
        feed_item = {}
        feed_item["addr"] = feed["contract"]
        feed_item["base_token"] = split_pair[0]
        feed_item["quote_token"] = split_pair[1]
        feed_item["source"] = feed["source"].capitalize()
        feed_item["timeframe"] = feed["timeframe"]
        feed_item["full_addr"] = feed["contract"]

        result = get_feeds_stat_with_contract(feed["contract"], feed_stats)

        feed_item.update(result)

        subscription_result = get_feeds_subscription_stat_with_contract(
            feed["contract"], feed_subcription_stats
        )

        feed_item.update(subscription_result)

        new_feed_data.append(feed_item)

    columns = get_feed_column_ids(new_feed_data[0])

    formatted_data = format_table(new_feed_data, columns)

    return columns, formatted_data, new_feed_data
