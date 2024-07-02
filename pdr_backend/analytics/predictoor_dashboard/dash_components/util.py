from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.lake.table_pdr_predictions import predictions_table_name


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
        """)
    

def get_predictoors_data_from_db(lake_dir):
    return _query_db(
        lake_dir,
        f"""
            SELECT user FROM {predictions_table_name}
            GROUP BY user
        """
        )

def get_predictoors_stake_data_from_db(lake_dir):
    return _query_db(
        lake_dir,
        f"""
            SELECT user, stake, slot, pair, timeframe, source FROM {predictions_table_name}
        """
        )
