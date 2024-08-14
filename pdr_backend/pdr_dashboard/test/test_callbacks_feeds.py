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


def test_feeds_table(setup_app_with_etl_sample_data, dash_duo):
    app = setup_app_with_etl_sample_data
    start_server_and_wait(dash_duo, app)

    _navigate_to_feeds_page(dash_duo)
    dash_duo.wait_for_element("#feeds_page_table table")

    table = dash_duo.find_element("#feeds_page_table table")

    # Validate row and column count
    rows = table.find_elements(By.XPATH, ".//tr")
    assert len(rows) == 21

    header = table.find_element(By.XPATH, ".//tr[1]")
    columns = header.find_elements(By.XPATH, ".//th")
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


def test_feeds_page_metrics_row(setup_app_with_etl_sample_data, dash_duo):
    app = setup_app_with_etl_sample_data
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


def test_feeds_table_filters(setup_app_with_etl_sample_data, dash_duo):
    app = setup_app_with_etl_sample_data
    start_server_and_wait(dash_duo, app)

    _navigate_to_feeds_page(dash_duo)
    dash_duo.wait_for_element("#base_token")

    # Test filtering with base token
    _set_dropdown_and_verify_row_count(dash_duo, "#base_token", "ETH", 3)

    # Test filtering with time
    _set_dropdown_and_verify_row_count(dash_duo, "#time", "5m", 2)

    _clear_filters(dash_duo)
    _assert_table_row_count(dash_duo, "#feeds_page_table", 21)

    # Test filtering with ADA base token and accuracy range
    _set_dropdown_and_verify_row_count(dash_duo, "#base_token", "ADA", 3)

    _clear_filters(dash_duo)
    # Test filtering with accuracy min value
    _set_input_value_and_submit(
        dash_duo, "#accuracy_dropdown", "#accuracy_min", "90", "#accuracy_button"
    )
    _assert_table_row_count(dash_duo, "#feeds_page_table", 1)

    # Test filtering with accuracy min value
    _set_input_value_and_submit(
        dash_duo, None, "#accuracy_min", "55", "#accuracy_button"
    )
    _assert_table_row_count(dash_duo, "#feeds_page_table", 2)

    # Test filtering with volume max value
    _set_input_value_and_submit(
        dash_duo, "#volume_dropdown", "#volume_max", "14000", "#volume_button"
    )
    _assert_table_row_count(dash_duo, "#feeds_page_table", 1)

    _clear_filters(dash_duo)
    _assert_table_row_count(dash_duo, "#feeds_page_table", 21)


def test_feeds_table_modal(setup_app_with_etl_sample_data, dash_duo):
    app = setup_app_with_etl_sample_data
    start_server_and_wait(dash_duo, app)

    _navigate_to_feeds_page(dash_duo)

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
    assert all(
        "selected" not in row.get_attribute("class")
        for row in table.find_elements(By.XPATH, ".//tr")
    )


def test_feeds_searchbar(setup_app_with_etl_sample_data, dash_duo):
    app = setup_app_with_etl_sample_data
    start_server_and_wait(dash_duo, app)

    _navigate_to_feeds_page(dash_duo)
    dash_duo.wait_for_element("#search-input-feeds-table")

    _set_searchbar_value(
        dash_duo, "#search-input-feeds-table", "ETH", "#feeds_page_table", 3
    )
    _set_searchbar_value(
        dash_duo, "#search-input-feeds-table", "ADA", "#feeds_page_table", 3
    )
    _set_searchbar_value(
        dash_duo, "#search-input-feeds-table", "6f3bc", "#feeds_page_table", 2
    )
    _set_searchbar_value(
        dash_duo, "#search-input-feeds-table", "NO_ROWS", "#feeds_page_table", 1
    )
