from enforce_typing import enforce_types

from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.lake.table_pdr_predictions import predictions_table_name
from pdr_backend.ppss.ppss import mock_ppss
from pdr_backend.lake.plutil import _object_list_to_df


def _prepare_test_db(tmpdir, sample_data, table_name=predictions_table_name):
    ppss = mock_ppss(
        [{"predict": "binance BTC/USDT c 5m", "train_on": "binance BTC/USDT c 5m"}],
        "sapphire-mainnet",
        str(tmpdir),
    )

    db = DuckDBDataStore(str(ppss.lake_ss.lake_dir))

    sample_data_df = _object_list_to_df(sample_data)
    db.insert_from_df(
        sample_data_df,
        table_name,
    )

    db.duckdb_conn.close()

    return ppss, sample_data_df


@enforce_types
def _clear_test_db(dir: str):
    db = DuckDBDataStore(dir)
    db.drop_table("pdr_payouts")
    db.drop_table("pdr_predictions")
    db.duckdb_conn.close()
