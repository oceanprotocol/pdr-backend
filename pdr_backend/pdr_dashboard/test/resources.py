import logging
import os
import re
import time
from unittest.mock import patch

import dash_bootstrap_components as dbc
from dash import Dash
from enforce_typing import enforce_types
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.lake.payout import Payout
from pdr_backend.lake.plutil import _object_list_to_df
from pdr_backend.lake.prediction import Prediction
from pdr_backend.lake.test.resources import create_sample_etl, create_sample_raw_data
from pdr_backend.pdr_dashboard.predictoor_dash import setup_app as setup_app_main
from pdr_backend.ppss.ppss import mock_ppss

logger = logging.getLogger(__name__)


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
    time.sleep(4)
    assert len(dash_duo.find_elements(f"{table_id} tbody tr")) == expected_rows


def _select_dropdown_option(dash_duo, dropdown_id, option_text):
    dropdown = dash_duo.find_element(dropdown_id)
    dropdown.click()
    options = dash_duo.find_elements(".VirtualizedSelectOption")
    for option in options:
        if option.text == option_text:
            option.click()
            break
    time.sleep(4)


def _assert_table_row_count(dash_duo, table_id, expected_count):
    table_rows = dash_duo.find_elements(f"{table_id} tbody tr")
    assert (
        len(table_rows) == expected_count
    ), f"Expected {expected_count} rows, got {len(table_rows)}"


def start_server_and_wait(dash_duo, app):
    """
    Start the server and wait for the elements to be rendered.
    """
    time.sleep(4)
    dash_duo.driver.set_window_size(1920, 1080)
    dash_duo.start_server(app)
    dash_duo.wait_for_element("#feeds_table")
    dash_duo.wait_for_element("#predictoors_table")
    dash_duo.wait_for_element("#feeds_table tbody tr")
    dash_duo.wait_for_element("#predictoors_table tbody tr")

    radio_items = dash_duo.find_element("#general-lake-date-period-radio-items")
    radio_items.find_element(By.XPATH, "//label[4]").click()

    time.sleep(4)


def _navigate_to_feeds_page(dash_duo):
    time.sleep(4)
    dash_duo.wait_for_element("#feeds")
    dash_duo.find_element("#feeds").click()
    time.sleep(4)


def _navigate_to_predictoors_page(dash_duo):
    time.sleep(4)
    dash_duo.wait_for_element("#predictoors")
    dash_duo.find_element("#predictoors").click()
    time.sleep(4)


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
    time.sleep(4)
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
    time.sleep(4)


def _set_searchbar_value(dash_duo, search_input_id, value, table_id, expected_rows):

    searchbar = dash_duo.find_element(search_input_id)
    searchbar.clear()
    searchbar.send_keys(Keys.BACKSPACE * 10)

    searchbar.send_keys(value)
    time.sleep(4)

    table = dash_duo.find_element(table_id)
    rows = table.find_elements(By.XPATH, ".//tr")
    assert len(rows) == expected_rows


def _add_css(app):
    style_css = ""
    # read the styles.css file and add it to the assets folder
    # Read the styles.css file
    with open("pdr_backend/pdr_dashboard/assets/styles.css", "r") as f:
        style_css = f.read()

    # Manually link the CSS file by embedding its contents in a <style> tag
    app.index_string = f"""
    <!DOCTYPE html>
    <html>
        <head>
            {{%metas%}}
            <title>{{%title%}}</title>
            {{%favicon%}}
            {{%css%}}
            <style>{style_css}</style>
        </head>
        <body>
            {{%app_entry%}}
            <footer>
                {{%config%}}
                {{%scripts%}}
                {{%renderer%}}
            </footer>
        </body>
    </html>
    """

    return app


def _prepare_sample_app(tmpdir, include_my_addresses=False):
    _clear_test_db(str(tmpdir))

    base_test_dir = os.path.join(
        os.path.dirname(__file__),
        "../../lake/test/",
    )
    str_dir = str(base_test_dir)

    sample_raw_data = create_sample_raw_data(
        str_dir,
    )

    etl, db, _ = create_sample_etl(
        sample_raw_data,
        _get_test_DuckDB,
        str(tmpdir),
        "2024-07-26_00:00",
        "2024-07-26_02:00",
        True,
    )

    etl.do_etl()

    db.duckdb_conn.close()

    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.config["suppress_callback_exceptions"] = True

    app = _add_css(app)

    if include_my_addresses:
        etl.ppss.predictoor_ss.set_my_addresses(
            ["0x016790c9d93e1a0ef9df43646b0c35a0e3242f0a"]
        )

    with patch(
        "pdr_backend.pdr_dashboard.util.db.calculate_tx_gas_fee_cost_in_OCEAN",
        return_value=0.2,
    ), patch(
        "pdr_backend.pdr_dashboard.util.db.fetch_token_prices",
        return_value={"ROSE": 0.05612, "OCEAN": 0.48521312000000005},
    ):
        setup_app_main(app, etl.ppss)
        app.data._fee_cost = 1.0

    return app
