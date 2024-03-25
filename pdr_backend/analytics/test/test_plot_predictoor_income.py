from unittest.mock import MagicMock, patch
import polars as pl
from pdr_backend.analytics.plot_predictoor_income import (
    load_data,
    process_data,
    plot_income_data,
)
from pdr_backend.lake.table_silver_pdr_predictions import (
    silver_pdr_predictions_table_name,
)


@patch("pdr_backend.analytics.plot_predictoor_income.st")
@patch("pdr_backend.ppss.ppss.PPSS")
@patch("pdr_backend.lake.gql_data_factory.GQLDataFactory")
@patch("pdr_backend.analytics.plot_predictoor_income.ETL")
def test_load_data(
    mock_etl_constructor,
    mock_gql_data_factory_constructor,
    mock_ppss_constructor,
    mock_st,
):
    # Mocking PPSS, GQLDataFactory, ETL, and related functions/classes
    mock_ppss = MagicMock()
    mock_gql_data_factory = MagicMock()
    mock_etl = MagicMock()
    mock_etl.tables = {
        silver_pdr_predictions_table_name: MagicMock(
            df=pl.DataFrame(
                {"user": ["user1", "user2"], "contract": ["contract1", "contract2"]}
            )
        )
    }

    # Mocking load_data internal calls
    mock_ppss_constructor.return_value = mock_ppss
    mock_gql_data_factory_constructor.return_value = mock_gql_data_factory
    mock_etl_constructor.return_value = mock_etl

    # Call the function
    result = load_data()

    # Assertions
    assert mock_st.spinner.called
    assert result.shape == (2, 2)


def test_process_data():
    # Mock DataFrame
    df = pl.DataFrame(
        {
            "user": ["user1", "user2", "user3", "user1", "user3"],
            "contract": [
                "contract1",
                "contract2",
                "contract3",
                "contract1",
                "contract3",
            ],
            "slot": [1, 2, 1, 2, 2],
            "sum_revenue": [100, 200, 0, 10, 20],
            "sum_revenue_df": [50, 150, 0, 5, 10],
            "sum_revenue_user": [30, 80, 0, 2, 4],
            "sum_revenue_stake": [20, 50, -50, 3, 6],
            "stake": [10, 30, 50, 2, 4],
            "payout": [90, 180, -50, 10, 20],
        }
    )

    # Call the function
    result = process_data(df, ["user1", "user3"], ["contract1", "contract3"])

    # Expected result
    expected_result = pl.DataFrame(
        {
            "slot": [1, 2],
            "revenue": [100, 30],
            "revenue_df": [50, 15],
            "revenue_user": [30, 6],
            "revenue_stake": [-30, 9],
            "sum_stake": [60, 6],
            "sum_payout": [40, 30],
        }
    )

    # Assertions
    assert result.equals(expected_result)


def test_plot_income_data():
    # Mock DataFrame
    df = pl.DataFrame(
        {
            "slot": [1, 2],
            "revenue": [100, 200],
            "revenue_df": [50, 150],
            "revenue_user": [30, 80],
            "revenue_stake": [20, 50],
            "sum_stake": [10, 30],
            "sum_payout": [90, 180],
        }
    )

    # Mock Axes
    mock_ax = MagicMock()

    # Call the function
    plot_income_data(df, mock_ax)

    # Assertions
    assert mock_ax.set_title.called
    assert mock_ax.plot.called
