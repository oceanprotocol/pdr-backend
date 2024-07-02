from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.lake.table_pdr_predictions import predictions_table_name


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
