import pytest
import dash_bootstrap_components as dbc

from dash import Dash
from selenium.webdriver.chrome.options import Options

from pdr_backend.lake.payout import mock_payouts, mock_payouts_related_with_predictions
from pdr_backend.lake.prediction import mock_daily_predictions, mock_first_predictions

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

from pdr_backend.analytics.predictoor_dashboard.dash_components.util import (
    get_feeds_data_from_db,
    get_predictoors_data_from_payouts,
    get_user_payouts_stats_from_db,
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
    return options


@pytest.fixture
def setup_app(
    tmpdir, _sample_daily_predictions, _sample_payouts_related_with_predictions
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

    style_css = ""
    # read the styles.css file and add it to the assets folder
    # Read the styles.css file
    with open("pdr_backend/analytics/predictoor_dashboard/assets/styles.css", "r") as f:
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

    app.layout = get_layout()
    app.lake_dir = ppss.lake_ss.lake_dir
    app.feeds_data = get_feeds_data_from_db(ppss.lake_ss.lake_dir)
    app.predictoors_data = get_predictoors_data_from_payouts(
        get_user_payouts_stats_from_db(ppss.lake_ss.lake_dir)
    )
    app.favourite_addresses = ppss.predictoor_ss.my_addresses
    get_callbacks(app)
    app.favourite_addresses = ppss.predictoor_ss.my_addresses

    return app
