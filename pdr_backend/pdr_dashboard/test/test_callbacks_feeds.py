import json
import time

from selenium.webdriver.common.by import By
from pdr_backend.pdr_dashboard.test.resources import (
    _navigate_to_feeds_page,
    _assert_table_row_count,
    start_server_and_wait,
    _clear_filters,
    _set_dropdown_and_verify_row_count,
    _set_input_value_and_submit,
    _remove_tags,
    _set_searchbar_value,
)


def _preapre_table_data_to_be_saved_as_json(table):
    rows = table.find_elements(By.XPATH, ".//tr")
    header = rows[0].find_elements(By.XPATH, ".//th")

    headers = [_remove_tags(th.text) for th in header]

    table_data = []

    for row in rows[1:]:  # Skip header row
        cells = row.find_elements(By.XPATH, ".//td")
        row_data = {headers[i]: _remove_tags(cells[i].text) for i in range(len(cells))}
        table_data.append(row_data)

    return table_data


def _verify_table_data(table, filename):
    table_data = _preapre_table_data_to_be_saved_as_json(table)
    with open("pdr_backend/pdr_dashboard/test/json_fixtures/" + filename) as f:
        expected_data = json.load(f)

    for _, row in enumerate(table_data):
        assert row in expected_data


def test_feeds_table(_sample_app, dash_duo):
    app = _sample_app
    start_server_and_wait(dash_duo, app)

    _navigate_to_feeds_page(dash_duo)
    dash_duo.wait_for_element("#feeds_page_table table")

    table = dash_duo.find_element("#feeds_page_table table")

    # Validate row and column count
    rows = table.find_elements(By.XPATH, ".//tr")
    assert len(rows) == 21

    header = rows[0].find_elements(By.XPATH, ".//th")
    columns = header
    assert len(columns) == 12

    # Validate headers
    header_texts = [_remove_tags(c.text) for c in columns]
    expected_headers = [
        "",
        "Addr",
        "Base Token",
        "Quote Token",
        "Exchange",
        "Time",
        "Avg Accuracy",
        "Avg Stake Per Epoch (Ocean)",
        "Volume (Ocean)",
        "Price (Ocean)",
        "Sales",
        "Sales Revenue (Ocean)",
    ]
    assert header_texts == expected_headers

    _verify_table_data(table, "expected_feeds_table_data.json")


def test_feeds_page_metrics_row(_sample_app, dash_duo):
    app = _sample_app
    start_server_and_wait(dash_duo, app)

    _navigate_to_feeds_page(dash_duo)
    dash_duo.wait_for_element("#feeds_page_metrics_row")

    metrics_row = dash_duo.find_element("#feeds_page_metrics_row")

    # Validate metrics
    # select first level divs
    metrics = metrics_row.find_elements(By.XPATH, "./div")
    assert len(metrics) == 5

    metric_texts = [_remove_tags(m.text) for m in metrics]
    expected_metrics = [
        "Feeds",
        "Accuracy",
        "Volume",
        "Sales",
        "Revenue",
    ]

    for i, metric in enumerate(expected_metrics):
        assert metric in metric_texts[i]


def test_feeds_table_filters(_sample_app, dash_duo):
    app = _sample_app
    start_server_and_wait(dash_duo, app)

    _navigate_to_feeds_page(dash_duo)
    dash_duo.wait_for_element("#feeds_page_table")
    dash_duo.wait_for_element("#base_token")

    table = dash_duo.find_element("#feeds_page_table table")

    # Test filtering with base token
    _set_dropdown_and_verify_row_count(dash_duo, "#base_token", "ETH", 3)
    _verify_table_data(table, "filtered_base_token_eth.json")

    # Test filtering with time
    _set_dropdown_and_verify_row_count(dash_duo, "#time", "5m", 2)
    _verify_table_data(table, "filtered_base_token_eth_5m.json")

    _clear_filters(dash_duo)
    _assert_table_row_count(dash_duo, "#feeds_page_table", 21)
    _verify_table_data(table, "expected_feeds_table_data.json")

    # Test filtering with ADA base token and accuracy range
    _set_dropdown_and_verify_row_count(dash_duo, "#base_token", "ADA", 3)
    _verify_table_data(table, "filtered_base_token_ada.json")

    _clear_filters(dash_duo)
    # Test filtering with accuracy min value
    _set_input_value_and_submit(
        dash_duo, "#accuracy_dropdown", "#accuracy_min", "90", "#accuracy_button"
    )
    _assert_table_row_count(dash_duo, "#feeds_page_table", 1)
    _verify_table_data(table, "filtered_accuracy_min_90.json")

    # Test filtering with accuracy min value
    _set_input_value_and_submit(
        dash_duo, None, "#accuracy_min", "55", "#accuracy_button"
    )
    _assert_table_row_count(dash_duo, "#feeds_page_table", 2)
    _verify_table_data(table, "filtered_accuracy_min_55.json")

    # Test filtering with volume max value
    _set_input_value_and_submit(
        dash_duo, "#volume_dropdown", "#volume_max", "14000", "#volume_button"
    )
    _assert_table_row_count(dash_duo, "#feeds_page_table", 1)
    _verify_table_data(table, "filtered_volume_max_1400.json")

    _clear_filters(dash_duo)
    _assert_table_row_count(dash_duo, "#feeds_page_table", 21)
    _verify_table_data(table, "expected_feeds_table_data.json")


def test_feeds_table_modal(_sample_app, dash_duo):
    app = _sample_app
    start_server_and_wait(dash_duo, app)

    _navigate_to_feeds_page(dash_duo)
    dash_duo.wait_for_element("#feeds_page_table")

    # Select a row
    table = dash_duo.find_element("#feeds_page_table")
    table.find_element(By.XPATH, "//tr[2]//td[1]//input[@type='radio']").click()
    time.sleep(1)

    base_token = table.find_element(By.XPATH, "//tr[2]//td[3]//div").text
    quote_token = table.find_element(By.XPATH, "//tr[2]//td[4]//div").text
    timeframe = table.find_element(By.XPATH, "//tr[2]//td[6]//div").text
    exchange = table.find_element(By.XPATH, "//tr[2]//td[5]//div").text

    dash_duo.wait_for_element("#modal", timeout=4)

    # Validate modal content
    modal = dash_duo.find_element("#modal")
    header_text = modal.find_element(
        By.XPATH, "//div[@id='feeds-modal-header']//span"
    ).text
    assert header_text == f"{base_token}-{quote_token} {timeframe} {exchange}"

    number_of_plots = len(
        modal.find_element(By.ID, "feeds-modal-body").find_elements(
            By.CLASS_NAME, "dash-graph"
        )
    )
    assert number_of_plots == 6

    # Close modal by clicking the background
    dash_duo.find_element(".modal").click()

    # Ensure no row is selected
    assert not any(
        "selected" in row.get_attribute("class")
        for row in table.find_elements(By.XPATH, ".//tr")
    )


def test_feeds_searchbar(_sample_app, dash_duo):
    app = _sample_app
    start_server_and_wait(dash_duo, app)

    _navigate_to_feeds_page(dash_duo)
    dash_duo.wait_for_element("#search-input-feeds-table")
    table = dash_duo.find_element("#feeds_page_table")
    _set_searchbar_value(
        dash_duo, "#search-input-feeds-table", "ETH", "#feeds_page_table", 3
    )
    _verify_table_data(table, "search_eth.json")

    _set_searchbar_value(
        dash_duo, "#search-input-feeds-table", "ADA", "#feeds_page_table", 3
    )
    _verify_table_data(table, "search_ada.json")

    _set_searchbar_value(
        dash_duo, "#search-input-feeds-table", "6f3bc", "#feeds_page_table", 2
    )
    _verify_table_data(table, "search_6f3bc.json")

    _set_searchbar_value(
        dash_duo, "#search-input-feeds-table", "NO_ROWS", "#feeds_page_table", 1
    )
    _verify_table_data(table, "search_no_rows.json")
