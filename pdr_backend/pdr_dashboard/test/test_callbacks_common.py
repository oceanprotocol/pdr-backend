import time
from datetime import UTC, datetime

from pdr_backend.pdr_dashboard.test.resources import start_server_and_wait


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


def test_set_period_start_date(_sample_app, dash_duo):
    app = _sample_app
    start_server_and_wait(dash_duo, app)

    # Default page is Home
    dash_duo.wait_for_element_by_id("plots_container", timeout=10)

    # Set period start date
    assert app.data.start_date is None
    dash_duo.find_elements("#general-lake-date-period-radio-items label")[0].click()
    time.sleep(1)
    assert app.data.start_date is not None

    delta = datetime.now(UTC) - app.data.start_date
    assert delta.days == 1
    assert delta.seconds < 120

    dash_duo.find_elements("#general-lake-date-period-radio-items label")[3].click()
    time.sleep(1)
    assert app.data.start_date is None
