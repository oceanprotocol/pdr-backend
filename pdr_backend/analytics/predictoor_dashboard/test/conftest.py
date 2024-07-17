import pytest
from selenium.webdriver.chrome.options import Options

from pdr_backend.lake.payout import mock_payouts, mock_payouts_related_with_predictions
from pdr_backend.lake.prediction import mock_daily_predictions, mock_first_predictions


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
