from unittest.mock import patch

from enforce_typing import enforce_types
import polars as pl

from pdr_backend.util.get_traction_info import get_traction_info_main
from pdr_backend.util.subgraph_predictions import FilterMode
from pdr_backend.util.timeutil import timestr_to_ut


@enforce_types
@patch("pdr_backend.util.get_traction_info.get_traction_statistics")
@patch("pdr_backend.data_eng.gql_data_factory.fetch_filtered_predictions")
@patch("pdr_backend.util.get_traction_info.plot_traction_cum_sum_statistics")
@patch("pdr_backend.util.get_traction_info.plot_traction_daily_statistics")
def test_get_traction_info_main_mainnet(
    mock_plot_traction_daily_statistics,
    mock_plot_traction_cum_sum_statistics,
    mock_fetch_filtered_predictions,
    mock_get_traction_statistics,
    mock_ppss_web3,
    sample_daily_predictions,
):
    mock_fetch_filtered_predictions.return_value = sample_daily_predictions

    st_timestr = "2023-11-02"
    fin_timestr = "2023-11-05"

    get_traction_info_main(mock_ppss_web3, st_timestr, fin_timestr, "parquet_data/")

    mock_fetch_filtered_predictions.assert_called_with(
        1698883200,
        1699142400,
        [],
        "mainnet",
        FilterMode.NONE,
        payout_only=False,
        trueval_only=False,
    )

    # calculate ms locally so we can filter raw Predictions
    st_ut = timestr_to_ut(st_timestr)
    fin_ut = timestr_to_ut(fin_timestr)
    st_ut_sec = st_ut // 1000
    fin_ut_sec = fin_ut // 1000

    # Get all predictions into a dataframe
    preds = [
        x for x in sample_daily_predictions if st_ut_sec <= x.timestamp <= fin_ut_sec
    ]
    preds = [pred.__dict__ for pred in preds]
    preds_df = pl.DataFrame(preds)
    preds_df = preds_df.with_columns(
        [
            pl.col("timestamp").mul(1000).alias("timestamp_ms"),
        ]
    )

    # Assert calls and values
    pl.DataFrame.equals(mock_get_traction_statistics.call_args, preds_df)
    mock_plot_traction_cum_sum_statistics.assert_called()
    mock_plot_traction_daily_statistics.assert_called()
