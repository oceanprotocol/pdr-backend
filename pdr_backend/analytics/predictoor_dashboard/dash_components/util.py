from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.lake.table_pdr_predictions import predictions_table_name
from pdr_backend.lake.table_pdr_payouts import payouts_table_name


def get_feeds_data_from_db(lake_dir):
    feed_data = {}
    db = DuckDBDataStore(lake_dir, read_only=True)
    try:
        df = db.query_data(
            f"""
                SELECT contract, pair, timeframe, source FROM {predictions_table_name}
                GROUP BY contract, pair, timeframe, source
            """
        )

        if len(df) == 0:
            return feed_data
        feed_data = df.to_dicts()
    except Exception as e:
        print(e)
    return feed_data


def get_predictoors_data_from_db(lake_dir):
    predictoor_data = {}
    db = DuckDBDataStore(lake_dir, read_only=True)
    try:
        df = db.query_data(
            f"""
                SELECT user FROM {predictions_table_name}
                GROUP BY user
            """
        )

        if len(df) == 0:
            return predictoor_data
        predictoor_data = df.to_dicts()
    except Exception as e:
        print(e)
    return predictoor_data


def get_payouts_from_db(feed_addrs, predictoor_addrs, lake_dir):
    payouts_data = {}
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
