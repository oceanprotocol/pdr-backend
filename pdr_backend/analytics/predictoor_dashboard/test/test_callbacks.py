import time
from pdr_backend.analytics.predictoor_dashboard.test.resources import (
    _input_action,
    start_server_and_wait,
)


def test_get_input_data_from_db(setup_app, dash_duo):
    app = setup_app
    start_server_and_wait(dash_duo, app)


def test_feeds_search_input(setup_app, dash_duo):
    """
    Test the search input in the "Feeds" table.
    The search input is used to filter the feeds by their name.
    """

    app = setup_app
    start_server_and_wait(dash_duo, app)
    _input_action(dash_duo, "#search-input-Feeds", "#feeds_table", "OCEAN", 1)
    _input_action(dash_duo, "#search-input-Feeds", "#feeds_table", "BTC", 2)
    _input_action(dash_duo, "#search-input-Feeds", "#feeds_table", "ADA", 2)


def test_predictoors_search_input(setup_app, dash_duo):
    """
    Test the search input in the "Predictoors" table.
    The search input is used to filter the predictoors by their name.
    """

    app = setup_app
    start_server_and_wait(dash_duo, app)

    _input_action(
        dash_duo, "#search-input-Predictoors", "#predictoors_table", "0xaaa", 1
    )
    _input_action(
        dash_duo, "#search-input-Predictoors", "#predictoors_table", "0xd2", 2
    )


def test_checkbox_selection(setup_app, dash_duo):
    """
    Test the selection of checkboxes in the "Feeds" and "Predictoors" tables.
    """

    app = setup_app
    start_server_and_wait(dash_duo, app)

    # click on the checkbox in the second row of the "Feeds" table
    dash_duo.find_element("#feeds_table tbody tr:nth-child(2) input").click()

    # click on the checkbox in the first row of the "Predictoors" table
    dash_duo.find_element("#predictoors_table tbody tr input").click()


def test_timeframe_metrics(setup_app, dash_duo):
    """
    Test the metrics that are displayed when a predictoor is selected.
    It takes the predictoor row from the table and compares with the top metrics.

    The metrics are: Profit, Accuract, Stake
    """

    app = setup_app
    start_server_and_wait(dash_duo, app)

    dash_duo.find_element("#predictoors_table tbody tr:nth-child(3) input").click()
    time.sleep(2)

    dash_duo.find_element("#feeds_table tbody tr:nth-child(2) input").click()
    time.sleep(2)

    table_profit = dash_duo.find_element(
        "#predictoors_table tbody tr:nth-child(3) td:nth-child(3)"
    ).text
    metric_profit = dash_duo.find_element("#profit_metric").text
    assert table_profit + " OCEAN" == metric_profit

    table_accuracy = dash_duo.find_element(
        "#predictoors_table tbody tr:nth-child(3) td:nth-child(4)"
    ).text
    metric_accuracy = dash_duo.find_element("#accuracy_metric").text
    assert table_accuracy + ".0%" == metric_accuracy

    table_stake = dash_duo.find_element(
        "#predictoors_table tbody tr:nth-child(3) td:nth-child(5)"
    ).text
    metric_stake = dash_duo.find_element("#stake_metric").text
    assert table_stake + " OCEAN" == metric_stake


def test_predictoors_feed_only_switch(setup_app, dash_duo):
    """
    Test the switch that toggles between showing only the feeds that are
    associated with the selected predictoor and all feeds.
    """

    app = setup_app
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
    assert feeds_table_len == 6
