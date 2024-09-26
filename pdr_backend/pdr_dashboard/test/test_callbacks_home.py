import time

from pdr_backend.pdr_dashboard.test.resources import (
    _input_action,
    start_server_and_wait,
)


def test_get_input_data_from_db(_sample_app, dash_duo):
    app = _sample_app
    start_server_and_wait(dash_duo, app)


def test_feeds_search_input(_sample_app, dash_duo):
    """
    Test the search input in the "Feeds" table.
    The search input is used to filter the feeds by their name.
    """

    app = _sample_app
    start_server_and_wait(dash_duo, app)

    _input_action(dash_duo, "#search-input-Feeds", "#feeds_table", "OCEAN", 1)
    _input_action(dash_duo, "#search-input-Feeds", "#feeds_table", "BTC", 3)
    _input_action(dash_duo, "#search-input-Feeds", "#feeds_table", "ADA", 3)


# pylint: disable=too-many-statements
def test_predictoors_search_input(_sample_app, dash_duo):
    """
    Test the search input in the "Predictoors" table.
    The search input is used to filter the predictoors by their name.
    """

    app = _sample_app
    start_server_and_wait(dash_duo, app)

    _input_action(
        dash_duo, "#search-input-Predictoors", "#predictoors_table", "0xaaa", 1
    )

    _input_action(
        dash_duo, "#search-input-Predictoors", "#predictoors_table", "0x768", 2
    )


def _feed_count(dash_duo):
    feed_rows = dash_duo.find_elements("#feeds_table tbody tr input")
    feed_selected_rows = dash_duo.find_elements("#feeds_table tbody tr input:checked")

    return feed_rows, feed_selected_rows


def _predictoor_count(dash_duo):
    predictoors_rows = dash_duo.find_elements("#predictoors_table tbody tr")
    predictoors_selected_rows = dash_duo.find_elements(
        "#predictoors_table tbody tr input:checked"
    )

    return predictoors_rows, predictoors_selected_rows


def test_favourite_addresses_search_input(
    _sample_app_with_favourite_addresses, dash_duo
):
    app = _sample_app_with_favourite_addresses
    start_server_and_wait(dash_duo, app)

    fav_addr_toggle = dash_duo.find_element("#show-favourite-addresses")
    all_feeds_toggle = dash_duo.find_element("#toggle-switch-predictoor-feeds")

    # default startup: one predictoor selected out of 6
    # and its single feed selected out of 5 total (ADA/USDT)
    p_all, p_sel = _predictoor_count(dash_duo)
    assert len(p_all) == 58
    assert len(p_sel) == 1
    f_all, f_sel = _feed_count(dash_duo)
    assert len(f_all) == 1
    assert len(f_sel) == 1

    # click on all feeds toggle to show all feeds
    all_feeds_toggle.click()
    time.sleep(2)
    f_all, f_sel = _feed_count(dash_duo)
    assert len(f_all) == 20
    assert len(f_sel) == 1

    # click on fav addr toggle to show all predictoors
    fav_addr_toggle.click()
    time.sleep(2)
    p_all, p_sel = _predictoor_count(dash_duo)
    assert len(p_sel) == 1


def test_checkbox_selection(_sample_app, dash_duo):
    """
    Test the selection of checkboxes in the "Feeds" and "Predictoors" tables.
    """

    app = _sample_app
    start_server_and_wait(dash_duo, app)

    time.sleep(2)
    # click on the checkbox in the second row of the "Feeds" table
    dash_duo.find_element("#feeds_table tbody tr:nth-child(2) input").click()

    time.sleep(2)
    # click on the checkbox in the first row of the "Predictoors" table
    dash_duo.find_element("#predictoors_table tbody tr:nth-child(2) input").click()


def test_timeframe_metrics(_sample_app, dash_duo):
    """
    Test the metrics that are displayed when a predictoor is selected.
    It takes the predictoor row from the table and compares with the top metrics.

    The metrics are: Profit, Accuract, Stake
    """

    app = _sample_app
    start_server_and_wait(dash_duo, app)

    dash_duo.find_element("#predictoors_table tbody tr:nth-child(3) input").click()
    time.sleep(2)

    dash_duo.find_element("#feeds_table tbody tr:nth-child(2) input").click()

    table_profit = dash_duo.find_element(
        "#predictoors_table tbody tr:nth-child(2) td:nth-child(3)"
    ).text
    metric_profit = dash_duo.find_element("#profit_metric").text
    assert table_profit + " OCEAN" == metric_profit

    table_accuracy = dash_duo.find_element(
        "#predictoors_table tbody tr:nth-child(2) td:nth-child(4)"
    ).text
    metric_accuracy = dash_duo.find_element("#accuracy_metric").text
    assert table_accuracy == metric_accuracy

    table_stake = dash_duo.find_element(
        "#predictoors_table tbody tr:nth-child(2) td:nth-child(5)"
    ).text
    metric_stake = dash_duo.find_element("#stake_metric").text
    assert table_stake + " OCEAN" == metric_stake


def test_predictoors_feed_only_switch(_sample_app, dash_duo):
    """
    Test the switch that toggles between showing only the feeds that are
    associated with the selected predictoor and all feeds.
    """

    app = _sample_app
    start_server_and_wait(dash_duo, app)

    dash_duo.find_element("#predictoors_table tbody tr:nth-child(3) input").click()
    time.sleep(2)

    feeds_table_len = len(dash_duo.find_elements("#feeds_table tbody tr"))
    assert feeds_table_len == 2

    # Scroll the toggle switch into view and click using JavaScript
    toggle_switch = dash_duo.find_element("#toggle-switch-predictoor-feeds")
    dash_duo.driver.execute_script("arguments[0].scrollIntoView(true);", toggle_switch)
    dash_duo.driver.execute_script("arguments[0].click();", toggle_switch)
    time.sleep(2)

    feeds_table_len = len(dash_duo.find_elements("#feeds_table tbody tr"))
    assert feeds_table_len == 21


def test_navigation(_sample_app, dash_duo):
    app = _sample_app
    start_server_and_wait(dash_duo, app)

    # Default page is Home
    dash_duo.wait_for_element_by_id("plots_container", timeout=10)

    # Navigate to Feeds
    dash_duo.wait_for_element("#navbar-container a[href='/feeds']").click()
    dash_duo.wait_for_element_by_id("feeds_page_metrics_row", timeout=10)
    dash_duo.wait_for_element_by_id("feeds_page_table", timeout=10)

    # Navigate to Home
    dash_duo.wait_for_element("#navbar-container a[href='/']").click()
    dash_duo.wait_for_element_by_id("plots_container", timeout=10)
