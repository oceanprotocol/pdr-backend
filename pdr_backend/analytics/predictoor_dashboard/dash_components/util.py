from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.lake.table_pdr_predictions import predictions_table_name
from pdr_backend.lake.table_pdr_payouts import payouts_table_name


def _query_db(lake_dir, query):
    try:
        db = DuckDBDataStore(lake_dir, read_only=True)
        df = db.query_data(query)
        if len(df) == 0:
            return {}
        return df.to_dicts()
    except Exception as e:
        print(e)
        return {}


def get_feeds_data_from_db(lake_dir):
    return _query_db(
        lake_dir,
        f"""
            SELECT contract, pair, timeframe, source FROM {predictions_table_name}
            GROUP BY contract, pair, timeframe, source
        """,
    )


def get_predictoors_data_from_db(lake_dir):
    return _query_db(
        lake_dir,
        f"""
            SELECT user FROM {predictions_table_name}
            GROUP BY user
        """,
    )


def get_predictoors_stake_data_from_db(lake_dir):
    return _query_db(
        lake_dir,
        f"""
            SELECT user, stake, slot, pair, timeframe, source FROM {predictions_table_name}
        """,
    )


def get_payouts_from_db(feed_addrs, predictoor_addrs, lake_dir):
    payouts_data = []
    db = DuckDBDataStore(lake_dir, read_only=True)

    # Constructing the SQL query
    query = f"SELECT * FROM {payouts_table_name} WHERE ("

    # Adding conditions for the first list
    query += " OR ".join([f"ID LIKE '%{item}%'" for item in feed_addrs])
    query += ") AND ("

    # Adding conditions for the second list
    query += " OR ".join([f"ID LIKE '%{item}%'" for item in predictoor_addrs])
    query += ");"

    try:
        df = db.query_data(query)

        if len(df) == 0:
            return payouts_data
        payouts_data = df.to_dicts()
    except Exception as e:
        print(e)
    return payouts_data
