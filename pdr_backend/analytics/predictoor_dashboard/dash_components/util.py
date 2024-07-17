import logging

from datetime import datetime, timedelta
from typing import Union, List, Dict, Any, Optional
from enforce_typing import enforce_types
import dash

from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.lake.payout import Payout
from pdr_backend.lake.prediction import Prediction

logger = logging.getLogger("predictoor_dashboard_utils")


@enforce_types
def _query_db(lake_dir: str, query: str) -> Union[List[dict], Exception]:
    """
    Query the database with the given query.
    Args:
        lake_dir (str): Path to the lake directory.
        query (str): SQL query.
    Returns:
        dict: Query result.
    """
    try:
        db = DuckDBDataStore(lake_dir, read_only=True)
        df = db.query_data(query)
        db.duckdb_conn.close()
        return df.to_dicts() if len(df) else []
    except Exception as e:
        logger.error("Error querying the database: %s", e)
        return []


@enforce_types
def get_feeds_data_from_db(lake_dir: str):
    return _query_db(
        lake_dir,
        f"""
            SELECT contract, pair, timeframe, source FROM {Prediction.get_lake_table_name()}
            GROUP BY contract, pair, timeframe, source
        """,
    )


@enforce_types
def get_predictoors_data_from_db(lake_dir: str):
    return _query_db(
        lake_dir,
        f"""
            SELECT user FROM {Prediction.get_lake_table_name()}
            GROUP BY user
        """,
    )


@enforce_types
def get_payouts_from_db(
    feed_addrs: List[str], predictoor_addrs: List[str], start_date: int, lake_dir: str
) -> List[dict]:
    """
    Get payouts data for the given feed and predictoor addresses.
    Args:
        feed_addrs (list): List of feed addresses.
        predictoor_addrs (list): List of predictoor addresses.
        lake_dir (str): Path to the lake directory.
    Returns:
        list: List of payouts data.
    """

    # Constructing the SQL query
    query = f"SELECT * FROM {Payout.get_lake_table_name()} WHERE ("

    # Adding conditions for the first list
    query += " OR ".join([f"ID LIKE '%{item}%'" for item in feed_addrs])
    query += ") AND ("

    # Adding conditions for the second list
    query += " OR ".join([f"ID LIKE '%{item}%'" for item in predictoor_addrs])
    query += ")"
    if start_date != 0:
        query += f"AND (slot > {start_date})"
    query += ";"

    return _query_db(lake_dir, query)


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
        if search_string.lower() in obj[field].lower() or obj in previous_objects
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


def get_start_date_from_period(period: int):
    return int((datetime.now() - timedelta(days=period)).timestamp())


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
