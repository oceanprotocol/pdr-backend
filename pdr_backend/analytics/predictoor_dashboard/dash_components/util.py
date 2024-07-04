from typing import Union, List
from enforce_typing import enforce_types

from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.lake.table_pdr_predictions import predictions_table_name
from pdr_backend.lake.table_pdr_payouts import payouts_table_name


@enforce_types
def _query_db(lake_dir: str, query: str) -> Union[dict, Exception]:
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
        db.close()
        if len(df) == 0:
            return {}
        return df.to_dicts()
    except Exception as e:
        return e


@enforce_types
def get_feeds_data_from_db(lake_dir: str):
    return _query_db(
        lake_dir,
        f"""
            SELECT contract, pair, timeframe, source FROM {predictions_table_name}
            GROUP BY contract, pair, timeframe, source
        """,
    )


@enforce_types
def get_predictoors_data_from_db(lake_dir: str):
    return _query_db(
        lake_dir,
        f"""
            SELECT user FROM {predictions_table_name}
            GROUP BY user
        """,
    )


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

    payouts_data: List[dict] = []

    # Constructing the SQL query
    query = f"SELECT * FROM {payouts_table_name} WHERE ("

    # Adding conditions for the first list
    query += " OR ".join([f"ID LIKE '%{item}%'" for item in feed_addrs])
    query += ") AND ("

    # Adding conditions for the second list
    query += " OR ".join([f"ID LIKE '%{item}%'" for item in predictoor_addrs])
    query += ");"

    try:
        db = DuckDBDataStore(lake_dir, read_only=True)
        df = db.query_data(query)
        db.close()
        if len(df) == 0:
            return payouts_data
        payouts_data = df.to_dicts()
    except Exception as e:
        print(e)
    return payouts_data


# Function to filter the list by field containing a given string
def filter_objects_by_field(objects, field, search_string):
    return list(
        filter(lambda obj: search_string.lower() in obj[field].lower(), objects)
    )
