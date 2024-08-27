import time
from selenium.webdriver.common.by import By
from pdr_backend.pdr_dashboard.test.resources import (
    _assert_table_row_count,
    _clear_predictoors_filters,
    _navigate_to_predictoors_page,
    _remove_tags,
    _set_input_value_and_submit,
    _set_searchbar_value,
    start_server_and_wait,
)
from pdr_backend.pdr_dashboard.test.test_callbacks_feeds import (
    _verify_table_data,
    _verify_table_data_order,
)


def test_predictoors_table(_sample_app, dash_duo):
    app = _sample_app
    start_server_and_wait(dash_duo, app)

    _navigate_to_predictoors_page(dash_duo)
    dash_duo.wait_for_element("#predictoors_page_table table")

    table = dash_duo.find_element("#predictoors_page_table table")

    # Validate row and column count
    rows = table.find_elements(By.XPATH, ".//tr")
    assert len(rows) == 58

    header = rows[0].find_elements(By.XPATH, ".//th")
    columns = header
    assert len(columns) == 10

    # Validate headers
    header_texts = [_remove_tags(c.text) for c in columns]
    expected_headers = [
        "",
        "Addr",
        "Apr",
        "Accuracy",
        "Number Of Feeds",
        "Staked (Ocean)",
        "Gross Income (Ocean)",
        "Net Income (Ocean)",
        "Stake Loss (Ocean)",
        "Tx Costs (Ocean)",
    ]
    assert header_texts == expected_headers

    _verify_table_data(table, "expected_predictoors_table_data.json")


def test_feeds_page_metrics_row(_sample_app, dash_duo):
    app = _sample_app
    start_server_and_wait(dash_duo, app)

    _navigate_to_predictoors_page(dash_duo)
    dash_duo.wait_for_element("#predictoors_page_metrics_row")

    metrics_row = dash_duo.find_element("#predictoors_page_metrics_row")

    # Validate metrics
    # select first level divs
    metrics = metrics_row.find_elements(By.XPATH, "./div")
    assert len(metrics) == 4

    metric_texts = [_remove_tags(m.text) for m in metrics]
    expected_metrics = [
        "Predictoors",
        "Accuracy(avg)",
        "Staked",
        "Gross Income",
    ]

    for i, metric in enumerate(expected_metrics):
        assert metric in metric_texts[i]


def test_predictoors_table_filters(_sample_app, dash_duo):
    app = _sample_app
    start_server_and_wait(dash_duo, app)

    _navigate_to_predictoors_page(dash_duo)
    dash_duo.wait_for_element("#predictoors_page_table")
    dash_duo.wait_for_element("#p_accuracy_dropdown")

    table = dash_duo.find_element("#predictoors_page_table table")

    _clear_predictoors_filters(dash_duo)
    # Test filtering with accuracy min value
    _set_input_value_and_submit(
        dash_duo, "#p_accuracy_dropdown", "#p_accuracy_min", "90", "#p_accuracy_button"
    )
    _assert_table_row_count(dash_duo, "#predictoors_page_table", 7)
    _verify_table_data(table, "filtered_p_accuracy_min_90.json")

    # Test filtering with accuracy min value
    _set_input_value_and_submit(
        dash_duo, None, "#p_accuracy_min", "55", "#p_accuracy_button"
    )
    _assert_table_row_count(dash_duo, "#predictoors_page_table", 17)
    _verify_table_data(table, "filtered_p_accuracy_min_55.json")

    # Test filtering with staked max value + natural language
    _set_input_value_and_submit(
        dash_duo, "#stake_dropdown", "#stake_max", "4K", "#stake_button"
    )
    _assert_table_row_count(dash_duo, "#predictoors_page_table", 5)
    _verify_table_data(table, "filtered_stake_max_4K.json")

    _clear_predictoors_filters(dash_duo)
    _assert_table_row_count(dash_duo, "#predictoors_page_table", 58)
    _verify_table_data(table, "expected_predictoors_table_data.json")


def test_predictoors_table_modal(_sample_app, dash_duo):
    app = _sample_app
    start_server_and_wait(dash_duo, app)

    _navigate_to_predictoors_page(dash_duo)
    dash_duo.wait_for_element("#predictoors_page_table")

    # Select a row
    table = dash_duo.find_element("#predictoors_page_table")
    table.find_element(By.XPATH, "//tr[2]//td[1]//input[@type='radio']").click()
    time.sleep(1)

    addr_short = table.find_element(By.XPATH, "//tr[2]//td[2]//div").text

    dash_duo.wait_for_element("#predictoors_modal", timeout=4)

    # Validate modal content
    modal = dash_duo.find_element("#predictoors_modal")
    header_text = modal.find_element(
        By.XPATH, "//div[@id='predictoors_modal-header']//span"
    ).text
    assert (
        header_text == addr_short[:5] + "..." + addr_short[-5:] + " - Predictoor Data"
    )

    number_of_plots = len(
        modal.find_element(By.ID, "predictoors_modal-body").find_elements(
            By.CLASS_NAME, "dash-graph"
        )
    )
    assert number_of_plots == 5

    # Close modal by clicking the background
    dash_duo.find_element(".modal").click()

    # Ensure no row is selected
    assert not any(
        "selected" in row.get_attribute("class")
        for row in table.find_elements(By.XPATH, ".//tr")
    )


def test_predictoors_searchbar(_sample_app, dash_duo):
    app = _sample_app
    start_server_and_wait(dash_duo, app)

    _navigate_to_predictoors_page(dash_duo)
    dash_duo.wait_for_element("#search-input-predictoors-table")
    table = dash_duo.find_element("#predictoors_page_table")

    _set_searchbar_value(
        dash_duo,
        "#search-input-predictoors-table",
        "xac8",
        "#predictoors_page_table",
        2,
    )
    _verify_table_data(table, "search_p_xac8.json")


def test_sort_table(_sample_app, dash_duo):
    app = _sample_app
    start_server_and_wait(dash_duo, app)

    _navigate_to_predictoors_page(dash_duo)

    # Wait for the table to be fully rendered
    dash_duo.wait_for_element("#predictoors_page_table")

    # Select the table element
    table = dash_duo.find_element("#predictoors_page_table")

    # Click the 'Staked' column header to sort
    actionables = table.find_elements(
        By.XPATH, "//div//div[@class='column-actions']//span"
    )[4]
    actionables.click()

    # Wait for the sort to apply
    time.sleep(1)  # Sometimes sorting might take a moment

    # Check if the data is sorted ascending
    _verify_table_data_order(table, "sorted_predictoors_table_asc_by_stake.json")

    # Click again to sort descending
    actionables.click()
    time.sleep(1)  # Wait for the sort to apply

    # Check if the data is sorted descending
    _verify_table_data_order(table, "sorted_predictoors_table_desc_by_stake.json")
