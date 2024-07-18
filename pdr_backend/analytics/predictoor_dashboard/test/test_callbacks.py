import time
from pdr_backend.analytics.predictoor_dashboard.test.resources import (
    _input_action,
)


def test_get_input_data_from_db(setup_app, dash_duo):
    app = setup_app
    start_server_and_wait(dash_duo, app)


def start_server_and_wait(dash_duo, app):
    dash_duo.start_server(app)
    dash_duo.wait_for_element("#feeds_table")
    dash_duo.wait_for_element("#predictoors_table")
    dash_duo.wait_for_element("#feeds_table tbody tr")
    dash_duo.wait_for_element("#predictoors_table tbody tr")


def test_feeds_search_input(setup_app, dash_duo):
    app = setup_app
    start_server_and_wait(dash_duo, app)
    _input_action(dash_duo, "#search-input-Feeds", "#feeds_table", "OCEAN", 1)
    _input_action(dash_duo, "#search-input-Feeds", "#feeds_table", "BTC", 2)
    _input_action(dash_duo, "#search-input-Feeds", "#feeds_table", "ADA", 2)


def test_predictoors_search_input(setup_app, dash_duo):
    app = setup_app
    start_server_and_wait(dash_duo, app)

    _input_action(
        dash_duo, "#search-input-Predictoors", "#predictoors_table", "0xaaa", 1
    )
    _input_action(
        dash_duo, "#search-input-Predictoors", "#predictoors_table", "0xd2", 2
    )


def test_checkbox_selection(setup_app, dash_duo):
    app = setup_app
    start_server_and_wait(dash_duo, app)

    # click on the checkbox in the second row of the "Feeds" table
    dash_duo.find_element("#feeds_table tbody tr:nth-child(2) input").click()

    # click on the checkbox in the first row of the "Predictoors" table
    dash_duo.find_element("#predictoors_table tbody tr input").click()


def test_timeframe_metrics(setup_app, dash_duo):
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
    app = setup_app
    start_server_and_wait(dash_duo, app)

    dash_duo.find_element("#predictoors_table tbody tr:nth-child(3) input").click()
    time.sleep(2)

    feeds_table_len = len(dash_duo.find_elements("#feeds_table tbody tr"))
    assert feeds_table_len == 2

    dash_duo.find_element("#toggle-switch-predictoor-feeds").click()
    time.sleep(2)

    feeds_table_len = len(dash_duo.find_elements("#feeds_table tbody tr"))
    assert feeds_table_len == 6
