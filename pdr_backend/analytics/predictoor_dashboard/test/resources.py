from enforce_typing import enforce_types

from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.ppss.ppss import mock_ppss
from pdr_backend.lake.plutil import _object_list_to_df
from pdr_backend.lake.prediction import Prediction
from pdr_backend.lake.payout import Payout


def _prepare_test_db(tmpdir, sample_data, table_name):
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
def _clear_test_db(directory: str):
    db = DuckDBDataStore(directory)
    db.drop_table(Payout.get_lake_table_name())
    db.drop_table(Prediction.get_lake_table_name())
    db.duckdb_conn.close()
