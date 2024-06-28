#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from unittest.mock import patch

import polars as pl
import pytest
from enforce_typing import enforce_types

from pdr_backend.analytics.get_predictions_info import get_traction_info_main
from pdr_backend.lake.prediction import Prediction
from pdr_backend.lake.table import NamedTable
from pdr_backend.ppss.ppss import mock_ppss


@enforce_types
@patch("pdr_backend.analytics.get_predictions_info.get_traction_statistics")
@patch("pdr_backend.analytics.get_predictions_info.plot_traction_cum_sum_statistics")
@patch("pdr_backend.analytics.get_predictions_info.plot_traction_daily_statistics")
@patch("pdr_backend.analytics.get_predictions_info.get_slot_statistics")
@patch("pdr_backend.analytics.get_predictions_info.plot_slot_daily_statistics")
def test_get_traction_info_main_mainnet(
    mock_plot_slot_daily_statistics,
    mock_get_slot_statistics,
    mock_plot_traction_daily_statistics,
    mock_plot_traction_cum_sum_statistics,
    mock_get_traction_statistics,
    _gql_datafactory_daily_predictions_df,
    tmpdir,
):
    st_timestr = "2023-11-02"
    fin_timestr = "2023-11-07"
    ppss = mock_ppss(
        [{"predict": "binance BTC/USDT c 5m", "train_on": "binance BTC/USDT c 5m"}],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    predictions_df = _gql_datafactory_daily_predictions_df
    predictions_table = NamedTable.from_dataclass(Prediction)
    predictions_table.append_to_storage(predictions_df, ppss)

    get_traction_info_main(ppss, st_timestr, fin_timestr)

    assert len(predictions_df) > 0

    # calculate ms locally so we can filter raw Predictions
    preds_df = predictions_df.filter(
        (predictions_df["timestamp"] >= ppss.lake_ss.st_timestamp)
        & (predictions_df["timestamp"] <= ppss.lake_ss.fin_timestamp)
    )

    assert len(predictions_df) == 6

    # Assert calls and values
    pl.DataFrame.equals(mock_get_traction_statistics.call_args, preds_df)

    # Assert all calls were made
    mock_plot_slot_daily_statistics.assert_called_once()
    mock_get_slot_statistics.assert_called_once()
    mock_plot_traction_daily_statistics.assert_called_once()
    mock_plot_traction_cum_sum_statistics.assert_called_once()
    mock_get_traction_statistics.assert_called_once()


@enforce_types
def test_get_traction_info_empty_data(
    tmpdir,
):
    st_timestr = "2023-11-02"
    fin_timestr = "2023-11-05"
    ppss = mock_ppss(
        [{"predict": "binance BTC/USDT c 5m", "train_on": "binance BTC/USDT c 5m"}],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    pdr_prediction_table = NamedTable.from_dataclass(Prediction)
    pdr_prediction_table.append_to_storage(
        pl.DataFrame([], schema=Prediction.get_lake_schema()), ppss
    )

    with pytest.raises(AssertionError):
        get_traction_info_main(ppss, st_timestr, fin_timestr)
