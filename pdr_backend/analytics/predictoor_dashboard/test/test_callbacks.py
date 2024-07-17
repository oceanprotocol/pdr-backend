import time
import pytest

from dash import Dash
import dash_bootstrap_components as dbc
from selenium.webdriver.common.keys import Keys

from pdr_backend.analytics.predictoor_dashboard.dash_components.callbacks import (
    get_callbacks,
)
from pdr_backend.analytics.predictoor_dashboard.dash_components.view_elements import (
    get_layout,
)
from pdr_backend.analytics.predictoor_dashboard.test.resources import (
    _prepare_test_db,
    _clear_test_db,
)
from pdr_backend.lake.payout import Payout
from pdr_backend.lake.prediction import Prediction


@pytest.fixture
def _test_analytics_app():
    app = Dash(__name__)
    get_callbacks(app)
    return app


def test_get_input_data_from_db(
    tmpdir,
    _sample_daily_predictions,
    _sample_payouts_related_with_predictions,
    dash_duo,
):
    _clear_test_db(str(tmpdir))

    _prepare_test_db(
        tmpdir,
        _sample_payouts_related_with_predictions,
        table_name=Payout.get_lake_table_name(),
    )

    ppss, _ = _prepare_test_db(
        tmpdir,
        _sample_daily_predictions,
        table_name=Prediction.get_lake_table_name(),
    )

    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.config["suppress_callback_exceptions"] = True
    app.layout = get_layout()
    get_callbacks(app)
    app.layout.children[0].data = ppss.lake_ss.lake_dir
    app.favourite_addresses = ppss.predictoor_ss.my_addresses

    dash_duo.start_server(app)
    dash_duo.wait_for_element("#feeds_table")
    dash_duo.wait_for_element("#predictoors_table")

    dash_duo.wait_for_element("#feeds_table tbody tr")
    dash_duo.wait_for_element("#predictoors_table tbody tr")

    # ----TEST SEARCH INPUT WITH "OCEAN" VALUE----#
    dash_duo.find_element("#search-input-Feeds").send_keys("OCEAN" + Keys.ENTER)
    # wait 5 seconds
    time.sleep(2)
    assert len(dash_duo.find_elements("#feeds_table tbody tr")) == 1

    # ----TEST SEARCH INPUT WITH "BTC" VALUE----#
    # reset the search input
    dash_duo.find_element("#search-input-Feeds").clear()
    # enter "BTC" phrase to the "search-input-Feeds" input
    dash_duo.find_element("#search-input-Feeds").send_keys("BTC" + Keys.ENTER)
    time.sleep(2)
    # check if the "Feeds" table has only two rows
    assert len(dash_duo.find_elements("#feeds_table tbody tr")) == 2

    # ----TEST SEARCH INPUT WITH "ADA" VALUE----#
    # reset the search input
    dash_duo.find_element("#search-input-Feeds").clear()
    # enter "BTC" phrase to the "search-input-Feeds" input
    dash_duo.find_element("#search-input-Feeds").send_keys("ADA" + Keys.ENTER)
    time.sleep(2)

    # check if the "Feeds" table has only two rows
    assert len(dash_duo.find_elements("#feeds_table tbody tr")) == 2

    # ----TEST PREDICTOOR INPUT WITH "0xaaa" VALUE----#
    dash_duo.find_element("#search-input-Predictoors").send_keys("0xaaa" + Keys.ENTER)
    time.sleep(2)
    assert len(dash_duo.find_elements("#predictoors_table tbody tr")) == 1

    # ----TEST PREDICTOOR INPUT WITH "0xd2" VALUE----#
    # clear input
    dash_duo.find_element("#search-input-Predictoors").clear()
    # enter "0xd2" phrase to the "search-input-Predictoors" input
    dash_duo.find_element("#search-input-Predictoors").send_keys("0xd2" + Keys.ENTER)
    time.sleep(2)

    # check if the "Predictoors" table has only one row
    assert len(dash_duo.find_elements("#predictoors_table tbody tr")) == 2

    # click on the checkbox in the second row of the "Feeds" table
    dash_duo.find_element("#feeds_table tbody tr:nth-child(2) input").click()

    # click on the checkbox in the first row of the "Predictoors" table
    dash_duo.find_element("#predictoors_table tbody tr input").click()
