import pytest
import polars as pl

from pdr_backend.subgraph.prediction import mock_daily_predictions
from pdr_backend.subgraph.subscription import mock_subscriptions
from pdr_backend.subgraph.trueval import mock_truevals
from pdr_backend.subgraph.payout import mock_payouts

from pdr_backend.lake.plutil import _object_list_to_df
from pdr_backend.lake.table_pdr_payouts import payouts_schema


@pytest.fixture()
def sample_daily_predictions():
    return mock_daily_predictions()


@pytest.fixture()
def sample_subscriptions():
    return mock_subscriptions()


@pytest.fixture()
def sample_truevals():
    return mock_truevals()


@pytest.fixture()
def sample_payouts():
    return mock_payouts()


@pytest.fixture()
def _gql_datafactory_sample_payouts_df():
    _payouts = mock_payouts()
    payouts_df = _object_list_to_df(_payouts, payouts_schema)
    payouts_df = payouts_df.with_columns(
        [pl.col("timestamp").mul(1000).alias("timestamp")]
    )

    return payouts_df
