import time
import re

from enforce_typing import enforce_types
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

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


def _get_test_DuckDB(directory):
    return DuckDBDataStore(directory)


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


def _select_dropdown_option(dash_duo, dropdown_id, option_text):
    dropdown = dash_duo.find_element(dropdown_id)
    dropdown.click()
    options = dash_duo.find_elements(".VirtualizedSelectOption")
    for option in options:
        if option.text == option_text:
            option.click()
            break


def _assert_table_row_count(dash_duo, table_id, expected_count):
    table_rows = dash_duo.find_elements(f"{table_id} tbody tr")
    assert len(table_rows) == expected_count


def start_server_and_wait(dash_duo, app):
    """
    Start the server and wait for the elements to be rendered.
    """

    dash_duo.start_server(app)
    dash_duo.wait_for_element("#feeds_table")
    dash_duo.wait_for_element("#predictoors_table")
    dash_duo.wait_for_element("#feeds_table tbody tr")
    dash_duo.wait_for_element("#predictoors_table tbody tr")


def _navigate_to_feeds_page(dash_duo):
    dash_duo.wait_for_element("#feeds")
    dash_duo.find_element("#feeds").click()


def _navigate_to_predictoors_page(dash_duo):
    dash_duo.wait_for_element("#predictoors")
    dash_duo.find_element("#predictoors").click()


def _remove_tags(text):
    """
    Removes HTML or XML tags from the input string.

    This function is useful for extracting plain text content from a string
    that contains HTML or XML markup, such as when processing lists of subelements
    within an HTML document.

    Parameters:
    text (str): The string from which HTML or XML tags should be removed.

    Returns:
    str: The input string with all HTML or XML tags removed.
    """
    clean = re.compile("<.*?>")
    return re.sub(clean, "", text)


def _clear_feeds_filters(dash_duo):
    dash_duo.find_element("#clear_feeds_filters_button").click()
    time.sleep(1)


def _clear_predictoors_filters(dash_duo):
    dash_duo.find_element("#clear_predictoors_filters_button").click()
    time.sleep(1)


def _set_dropdown_and_verify_row_count(
    dash_duo, dropdown_id, option_text, expected_row_count
):
    _select_dropdown_option(dash_duo, dropdown_id, option_text)
    _assert_table_row_count(dash_duo, "#feeds_page_table", expected_row_count)


def _set_input_value_and_submit(
    dash_duo, dropdown_id, input_id, value, submit_button_id
):
    if dropdown_id:
        dash_duo.find_element(dropdown_id).click()

    input_field = dash_duo.find_element(input_id)
    input_field.clear()
    input_field.send_keys(Keys.BACKSPACE * 2)
    input_field.send_keys(value + Keys.ENTER)
    dash_duo.find_element(submit_button_id).click()
    time.sleep(1)


def _set_searchbar_value(dash_duo, search_input_id, value, table_id, expected_rows):

    searchbar = dash_duo.find_element(search_input_id)
    searchbar.clear()
    searchbar.send_keys(Keys.BACKSPACE * 10)

    searchbar.send_keys(value)
    time.sleep(1)

    table = dash_duo.find_element(table_id)
    rows = table.find_elements(By.XPATH, ".//tr")
    assert len(rows) == expected_rows
