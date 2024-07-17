import logging

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
def get_user_payouts_stats_from_db(lake_dir: str):
    return _query_db(
        lake_dir,
        f"""
            SELECT 
                "user",
                SUM(payout - stake) AS total_profit,
                SUM(CASE WHEN payout > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS avg_accuracy,
                AVG(stake) AS avg_stake
            FROM 
                {Payout.get_lake_table_name()}
            GROUP BY 
                "user" 
        """,
    )


def get_feed_ids_based_on_predictoors_from_db(
    lake_dir: str, predictoor_addrs: List[str]
):
    # Constructing the SQL query
    query = f"""
        SELECT LIST(LEFT(ID, POSITION('-' IN ID) - 1)) as feed_addrs
        FROM {Payout.get_lake_table_name()}
        WHERE ID IN (
            SELECT MIN(ID)
            FROM {Payout.get_lake_table_name()}
            WHERE (
                {" OR ".join([f"ID LIKE '%{item}%'" for item in predictoor_addrs])}
            )
            GROUP BY LEFT(ID, POSITION('-' IN ID) - 1)
        );
    """

    # Execute the query
    return _query_db(lake_dir, query)[0]["feed_addrs"]


@enforce_types
def get_payouts_from_db(
    feed_addrs: List[str], predictoor_addrs: List[str], lake_dir: str
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
    query += ");"

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


@enforce_types
def merge_payout_stats_with_predictoors(
    user_payout_stats: List[Dict[str, Any]],
    predictoors_data: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Process the user payouts stats data.
    Args:
        user_payout_stats (list): List of user payouts stats data.
    Returns:
        list: List of processed user payouts stats data.
    """

    if user_payout_stats:
        # For each data element, matching user_payout_stat is found and updated.
        # If there is no match, the original data element is preserved.
        predictoors_data = [
            {
                **data,
                **next(
                    (
                        user_payout_stat
                        for user_payout_stat in user_payout_stats
                        if user_payout_stat["user"] == data["user"]
                    ),
                    {},
                ),
            }
            for data in predictoors_data
        ]

        # shorten the user address
        for data in predictoors_data:
            new_data = {
                "user_address": data["user"][:5] + "..." + data["user"][-5:],
                "total_profit": round(data["total_profit"], 2),
                "avg_accuracy": round(data["avg_accuracy"], 2),
                "avg_stake": round(data["avg_stake"], 2),
                "user": data["user"],
            }

            data.clear()
            data.update(new_data)

    return predictoors_data
