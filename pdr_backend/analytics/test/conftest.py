import pytest
import polars as pl

from pdr_backend.subgraph.prediction import (
    mock_daily_predictions,
    mock_first_predictions,
    mock_second_predictions,
)

from pdr_backend.lake.table_pdr_predictions import (
    _object_list_to_df,
    predictions_schema,
)


@pytest.fixture()
def _sample_first_predictions():
    return mock_first_predictions()


@pytest.fixture()
def _sample_second_predictions():
    return mock_second_predictions()


@pytest.fixture()
def _sample_daily_predictions():
    return mock_daily_predictions()


@pytest.fixture()
def _gql_datafactory_first_predictions_df():
    _predictions = mock_first_predictions()
    predictions_df = _object_list_to_df(_predictions, predictions_schema)
    predictions_df = predictions_df.with_columns(
        [pl.col("timestamp").mul(1000).alias("timestamp")]
    )

    return predictions_df


@pytest.fixture()
def _gql_datafactory_second_predictions_df():
    _predictions = mock_second_predictions()
    predictions_df = _object_list_to_df(_predictions, predictions_schema)
    predictions_df = predictions_df.with_columns(
        [pl.col("timestamp").mul(1000).alias("timestamp")]
    )

    return predictions_df


@pytest.fixture()
def _gql_datafactory_daily_predictions_df():
    _predictions = mock_daily_predictions()
    predictions_df = _object_list_to_df(_predictions, predictions_schema)
    predictions_df = predictions_df.with_columns(
        [pl.col("timestamp").mul(1000).alias("timestamp")]
    )

    return predictions_df
