from typing import List
from unittest.mock import patch

import polars as pl
from enforce_typing import enforce_types

from pdr_backend.analytics.predictoor_stats import (
    aggregate_prediction_statistics,
    calculate_slot_daily_statistics,
    get_feed_summary_stats,
    get_predictoor_summary_stats,
    get_endpoint_statistics,
    get_slot_statistics,
    get_traction_statistics,
    plot_slot_daily_statistics,
    plot_traction_cum_sum_statistics,
    plot_traction_daily_statistics,
)


@enforce_types
def test_aggregate_prediction_statistics(_sample_first_predictions):
    stats, correct_predictions = aggregate_prediction_statistics(
        _sample_first_predictions
    )
    assert isinstance(stats, dict)
    assert "pair_timeframe" in stats
    assert "predictor" in stats
    assert correct_predictions == 1  # Adjust based on your sample data


@enforce_types
def test_get_endpoint_statistics(_sample_first_predictions):
    accuracy, pair_timeframe_stats, predictoor_stats = get_endpoint_statistics(
        _sample_first_predictions
    )
    assert isinstance(accuracy, float)
    assert isinstance(pair_timeframe_stats, List)  # List[PairTimeframeStat]
    assert isinstance(predictoor_stats, List)  # List[PredictoorStat]
    for pair_timeframe_stat in pair_timeframe_stats:
        for key in [
            "pair",
            "timeframe",
            "accuracy",
            "stake",
            "payout",
            "number_of_predictions",
        ]:
            assert key in pair_timeframe_stat

    for predictoor_stat in predictoor_stats:
        for key in [
            "predictoor_address",
            "accuracy",
            "stake",
            "payout",
            "number_of_predictions",
            "details",
        ]:
            assert key in predictoor_stat
        assert len(predictoor_stat["details"]) == 2


@enforce_types
def test_get_feed_statistics(capsys, _sample_first_predictions):
    get_feed_summary_stats(_sample_first_predictions)
    captured = capsys.readouterr()
    output = captured.out
    assert "Overall Accuracy" in output
    assert "Accuracy for Pair" in output
    assert "Accuracy for Predictoor Address" in output


@enforce_types
def test_get_predictoor_statistics(capsys, _sample_first_predictions):
    get_predictoor_summary_stats(_sample_first_predictions)
    captured = capsys.readouterr()
    output = captured.out
    assert "Overall Accuracy" in output
    assert "Accuracy for Pair" in output
    assert "Accuracy for Predictoor Address" in output


@enforce_types
@patch("matplotlib.pyplot.savefig")
def test_get_traction_statistics(
    mock_savefig, _sample_first_predictions, _sample_second_predictions
):
    predictions = _sample_first_predictions + _sample_second_predictions

    # Get all predictions into a dataframe
    preds_dicts = [pred.__dict__ for pred in predictions]
    preds_df = pl.DataFrame(preds_dicts)

    stats_df = get_traction_statistics(preds_df)
    assert isinstance(stats_df, pl.DataFrame)
    assert stats_df.shape == (3, 3)
    assert "datetime" in stats_df.columns
    assert "daily_unique_predictoors_count" in stats_df.columns
    assert stats_df["cum_daily_unique_predictoors_count"].to_list() == [2, 3, 4]

    pq_dir = "parquet_data/"
    plot_traction_daily_statistics(stats_df, pq_dir)
    plot_traction_cum_sum_statistics(stats_df, pq_dir)

    assert mock_savefig.call_count == 2


@enforce_types
def test_get_slot_statistics(_sample_first_predictions, _sample_second_predictions):
    predictions = _sample_first_predictions + _sample_second_predictions

    # Get all predictions into a dataframe
    preds_dicts = [pred.__dict__ for pred in predictions]
    preds_df = pl.DataFrame(preds_dicts)

    # calculate slot stats
    slots_df = get_slot_statistics(preds_df)
    assert isinstance(slots_df, pl.DataFrame)
    assert slots_df.shape == (7, 9)

    for key in [
        "datetime",
        "pair",
        "timeframe",
        "slot",
        "pair_timeframe",
        "n_predictoors",
        "slot_stake",
        "slot_payout",
    ]:
        assert key in slots_df.columns

    assert slots_df["slot_payout"].to_list() == [0.0, 0.05, 0.05, 0.0, 0.0, 0.0, 0.1]
    assert slots_df["slot_stake"].to_list() == [0.05, 0.05, 0.05, 0.05, 0.05, 0.0, 0.1]


@enforce_types
@patch("matplotlib.pyplot.savefig")
def test_plot_slot_statistics(
    mock_savefig, _sample_first_predictions, _sample_second_predictions
):
    predictions = _sample_first_predictions + _sample_second_predictions

    # Get all predictions into a dataframe
    preds_dicts = [pred.__dict__ for pred in predictions]
    preds_df = pl.DataFrame(preds_dicts)

    # calculate slot stats
    slots_df = get_slot_statistics(preds_df)
    slot_daily_df = calculate_slot_daily_statistics(slots_df)

    for key in [
        "datetime",
        "daily_average_stake",
        "daily_average_payout",
        "daily_average_predictoor_count",
    ]:
        assert key in slot_daily_df.columns

    assert slot_daily_df["daily_average_stake"].round(2).to_list() == [0.1, 0.1, 0.15]
    assert slot_daily_df["daily_average_payout"].round(2).to_list() == [0.0, 0.05, 0.15]
    assert slot_daily_df["daily_average_predictoor_count"].round(2).to_list() == [
        1.0,
        1.0,
        1.0,
    ]

    pq_dir = "parquet_data/"
    plot_slot_daily_statistics(slots_df, pq_dir)

    assert mock_savefig.call_count == 2
