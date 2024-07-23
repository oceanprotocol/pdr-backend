import time

from enforce_typing import enforce_types
from selenium.webdriver.common.keys import Keys

from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.ppss.ppss import mock_ppss
from pdr_backend.lake.plutil import _object_list_to_df
from pdr_backend.lake.prediction import Prediction
from pdr_backend.lake.payout import Payout


def _prepare_test_db(tmpdir, sample_data, table_name, my_addresses=None):
    ppss = mock_ppss(
        [{"predict": "binance BTC/USDT c 5m", "train_on": "binance BTC/USDT c 5m"}],
        "sapphire-mainnet",
        str(tmpdir),
        my_addresses=my_addresses if my_addresses else [],
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


def _input_action(dash_duo, input_id, table_id, input_value, expected_rows):
    """
    Helper function to test the search input in the tables
    It sends the input_value to the search input and checks
    if the number of rows in the table is as expected
    """

    search_input = dash_duo.find_element(input_id)
    search_input.clear()
    search_input.send_keys(input_value + Keys.ENTER)
    time.sleep(2)
    assert len(dash_duo.find_elements(f"{table_id} tbody tr")) == expected_rows


def start_server_and_wait(dash_duo, app):
    """
    Start the server and wait for the elements to be rendered.
    """

    dash_duo.start_server(app)
    dash_duo.wait_for_element("#feeds_table")
    dash_duo.wait_for_element("#predictoors_table")
    dash_duo.wait_for_element("#feeds_table tbody tr")
    dash_duo.wait_for_element("#predictoors_table tbody tr")
