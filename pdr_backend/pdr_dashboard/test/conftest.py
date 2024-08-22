import os
from unittest.mock import patch

import dash_bootstrap_components as dbc
import pytest
from dash import Dash
from selenium.webdriver.chrome.options import Options

from pdr_backend.lake.payout import (
    Payout,
    mock_payouts,
    mock_payouts_related_with_predictions,
)
from pdr_backend.lake.prediction import (
    Prediction,
    mock_daily_predictions,
    mock_first_predictions,
)
from pdr_backend.lake.subscription import Subscription, mock_subscriptions
from pdr_backend.lake.test.resources import create_sample_etl, create_sample_raw_data
from pdr_backend.pdr_dashboard.predictoor_dash import setup_app as setup_app_main
from pdr_backend.pdr_dashboard.test.resources import (
    _clear_test_db,
    _get_test_DuckDB,
    _prepare_test_db,
)


@pytest.fixture()
def _sample_first_predictions():
    return mock_first_predictions()


@pytest.fixture()
def _sample_daily_predictions():
    return mock_daily_predictions()


@pytest.fixture()
def _sample_payouts():
    return mock_payouts()


@pytest.fixture()
def _sample_subscriptions():
    return mock_subscriptions()


@pytest.fixture()
def _sample_payouts_related_with_predictions():
    return mock_payouts_related_with_predictions()


# Test for select_or_clear_all_by_table function
@pytest.fixture
def sample_table_rows():
    return [
        {"name": "Alice", "age": 30, "city": "New York"},
        {"name": "Bob", "age": 24, "city": "San Francisco"},
        {"name": "Charlie", "age": 29, "city": "Boston"},
        {"name": "David", "age": 34, "city": "Chicago"},
        {"name": "Eve", "age": 28, "city": "Los Angeles"},
    ]


def pytest_setup_options():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-search-engine-choice-screen")

    return options


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


@pytest.fixture
def setup_app(
    tmpdir,
    _sample_daily_predictions,
    _sample_payouts_related_with_predictions,
    _sample_subscriptions,
):
    _clear_test_db(str(tmpdir))

    _prepare_test_db(
        tmpdir,
        _sample_payouts_related_with_predictions,
        table_name=Payout.get_lake_table_name(),
    )

    _prepare_test_db(
        tmpdir,
        _sample_subscriptions,
        table_name=Subscription.get_lake_table_name(),
    )

    ppss, _ = _prepare_test_db(
        tmpdir,
        _sample_daily_predictions,
        table_name=Prediction.get_lake_table_name(),
    )

    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.config["suppress_callback_exceptions"] = True

    app = _add_css(app)

    with patch(
        "pdr_backend.pdr_dashboard.predictoor_dash.calculate_tx_gas_fee_cost_in_OCEAN",
        return_value=0.2,
    ):
        setup_app_main(app, ppss)

    return app


@pytest.fixture
def setup_app_with_favourite_addresses(
    tmpdir,
    _sample_daily_predictions,
    _sample_payouts_related_with_predictions,
    _sample_subscriptions,
):
    _clear_test_db(str(tmpdir))

    _prepare_test_db(
        tmpdir,
        _sample_payouts_related_with_predictions,
        table_name=Payout.get_lake_table_name(),
    )

    _prepare_test_db(
        tmpdir,
        _sample_subscriptions,
        table_name=Subscription.get_lake_table_name(),
    )

    ppss, _ = _prepare_test_db(
        tmpdir,
        _sample_daily_predictions,
        table_name=Prediction.get_lake_table_name(),
        my_addresses=["0x7149ceca72c61991018ed80788bea3f3f4540c3c"],
    )

    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.config["suppress_callback_exceptions"] = True

    app = _add_css(app)
    with patch(
        "pdr_backend.pdr_dashboard.predictoor_dash.calculate_tx_gas_fee_cost_in_OCEAN",
        return_value=0.2,
    ):
        setup_app_main(app, ppss)

    return app


@pytest.fixture
def _sample_app(tmpdir):
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
        False,
    )

    db.duckdb_conn.close()

    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.config["suppress_callback_exceptions"] = True

    app = _add_css(app)
    with patch(
        "pdr_backend.pdr_dashboard.predictoor_dash.calculate_tx_gas_fee_cost_in_OCEAN",
        return_value=0.2,
    ):
        setup_app_main(app, etl.ppss)

    return app
