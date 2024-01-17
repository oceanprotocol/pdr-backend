import pytest

from pdr_backend.subgraph.prediction import mock_daily_predictions
from pdr_backend.subgraph.subscription import mock_subscriptions
from pdr_backend.subgraph.payout import mock_payouts


@pytest.fixture()
def sample_daily_predictions():
    return mock_daily_predictions()


@pytest.fixture()
def sample_subscriptions():
    return mock_subscriptions()


@pytest.fixture()
def sample_payouts():
    return mock_payouts()
