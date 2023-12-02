from typing import List

from enforce_typing import enforce_types
import polars as pl

from pdr_backend.util.predictoor_stats import (
    aggregate_prediction_statistics,
    get_endpoint_statistics,
    get_cli_statistics,
    get_traction_statistics,
    get_slot_statistics,
    plot_slot_daily_statistics,
)


@enforce_types
def test_aggregate_prediction_statistics(sample_first_predictions):
    stats, correct_predictions = aggregate_prediction_statistics(sample_first_predictions)
    assert isinstance(stats, dict)
    assert "pair_timeframe" in stats
    assert "predictor" in stats
    assert correct_predictions == 1  # Adjust based on your sample data


@enforce_types
def test_get_endpoint_statistics(sample_first_predictions):
    accuracy, pair_timeframe_stats, predictoor_stats = get_endpoint_statistics(
        sample_first_predictions
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
def test_get_cli_statistics(capsys, sample_first_predictions):
    get_cli_statistics(sample_first_predictions)
    captured = capsys.readouterr()
    output = captured.out
    assert "Overall Accuracy" in output
    assert "Accuracy for Pair" in output
    assert "Accuracy for Predictoor Address" in output


@enforce_types
def test_get_traction_statistics(sample_first_predictions, sample_second_predictions):
    predictions = sample_first_predictions + sample_second_predictions
    stats_df = get_traction_statistics(predictions)
    assert isinstance(stats_df, pl.DataFrame)
    assert stats_df.shape == (3, 3)
    assert "datetime" in stats_df.columns
    assert "daily_unique_predictoors_count" in stats_df.columns
    assert stats_df["cum_daily_unique_predictoors_count"].to_list() == [2, 3, 4]


@enforce_types
def test_get_slot_statistics(sample_first_predictions, sample_second_predictions):
    predictions = sample_first_predictions + sample_second_predictions
    stats_df = get_slot_statistics(predictions)
    assert isinstance(stats_df, pl.DataFrame)
    assert stats_df.shape == (7, 9)

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
        assert key in stats_df.columns

    assert stats_df["slot_payout"].to_list() == [0.0, 0.05, 0.05, 0.0, 0.0, 0.0, 0.05]
    assert stats_df["slot_stake"].to_list() == [0.05, 0.05, 0.05, 0.05, 0.05, 0.0, 0.05]


@enforce_types
def test_plot_slot_statistics(sample_first_predictions, sample_second_predictions, sample_third_predictions):
    predictions = sample_first_predictions + sample_second_predictions + sample_first_predictions
    stats_df = get_slot_statistics(predictions)
    
    plot_slot_daily_statistics("csvs/", stats_df)
