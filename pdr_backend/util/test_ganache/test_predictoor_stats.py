from typing import List, Set
from enforce_typing import enforce_types
import polars as pl

from pdr_backend.util.predictoor_stats import (
    aggregate_prediction_statistics,
    get_endpoint_statistics,
    get_cli_statistics,
    get_traction_statistics,
    get_slot_statistics,
)

from pdr_backend.util.subgraph_predictions import (
    Prediction,
)

sample_predictions = [
    Prediction(
        id="1",
        pair="ADA/USDT",
        timeframe="5m",
        prediction=True,
        stake=0.0500,
        trueval=False,
        timestamp=1701503000,
        source="binance",
        payout=0.0,
        slot=1701503100,
        user="0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
    Prediction(
        id="2",
        pair="ADA/USDT",
        timeframe="5m",
        prediction=False,
        stake=0.0500,
        trueval=True,
        timestamp=1701589400,
        source="binance",
        payout=0.0,
        slot=1701589500,
        user="0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
]


@enforce_types
def test_aggregate_prediction_statistics():
    stats, correct_predictions = aggregate_prediction_statistics(sample_predictions)
    assert isinstance(stats, dict)
    assert "pair_timeframe" in stats
    assert "predictor" in stats
    assert correct_predictions == 1  # Adjust based on your sample data


@enforce_types
def test_get_endpoint_statistics():
    accuracy, pair_timeframe_stats, predictoor_stats = get_endpoint_statistics(
        sample_predictions
    )
    assert isinstance(accuracy, float)
    assert isinstance(pair_timeframe_stats, List)  # List[PairTimeframeStat]
    assert isinstance(predictoor_stats, List)  # List[PredictoorStat]
    for pair_timeframe_stat in pair_timeframe_stats:
        assert isinstance(pair_timeframe_stat, dict)
        assert "pair" in pair_timeframe_stat and isinstance(
            pair_timeframe_stat["pair"], str
        )
        assert "timeframe" in pair_timeframe_stat and isinstance(
            pair_timeframe_stat["timeframe"], str
        )
        assert "accuracy" in pair_timeframe_stat and isinstance(
            pair_timeframe_stat["accuracy"], float
        )
        assert "stake" in pair_timeframe_stat and isinstance(
            pair_timeframe_stat["stake"], float
        )
        assert "payout" in pair_timeframe_stat and isinstance(
            pair_timeframe_stat["payout"], float
        )
        assert "number_of_predictions" in pair_timeframe_stat and isinstance(
            pair_timeframe_stat["number_of_predictions"], int
        )

    for predictoor_stat in predictoor_stats:
        assert isinstance(predictoor_stat, dict) and len(predictoor_stat) == 6
        assert "predictoor_address" in predictoor_stat and isinstance(
            predictoor_stat["predictoor_address"], str
        )
        assert "accuracy" in predictoor_stat and isinstance(
            predictoor_stat["accuracy"], float
        )
        assert "stake" in predictoor_stat and isinstance(
            predictoor_stat["stake"], float
        )
        assert "payout" in predictoor_stat and isinstance(
            predictoor_stat["payout"], float
        )
        assert "number_of_predictions" in predictoor_stat and isinstance(
            predictoor_stat["number_of_predictions"], int
        )
        assert "details" in predictoor_stat and isinstance(
            predictoor_stat["details"], Set
        )
        assert len(predictoor_stat["details"]) == 1


@enforce_types
def test_get_cli_statistics(capsys):
    get_cli_statistics(sample_predictions)
    captured = capsys.readouterr()
    output = captured.out
    assert "Overall Accuracy" in output
    assert "Accuracy for Pair" in output
    assert "Accuracy for Predictoor Address" in output


extra_predictions = [
    Prediction(
        id="3",
        pair="ETH/USDT",
        timeframe="5m",
        prediction=True,
        stake=0.0500,
        trueval=True,
        timestamp=1701675800,
        source="binance",
        payout=0.0500,
        slot=1701675900,
        user="0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
    Prediction(
        id="4",
        pair="BTC/USDT",
        timeframe="1h",
        prediction=True,
        stake=0.0500,
        trueval=False,
        timestamp=1701503100,
        source="binance",
        payout=0.0,
        slot=1701503000,
        user="0xbbbb4cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
    Prediction(
        id="5",
        pair="ADA/USDT",
        timeframe="5m",
        prediction=True,
        stake=0.0500,
        trueval=True,
        timestamp=1701589400,
        source="binance",
        payout=0.0500,
        slot=1701589500,
        user="0xbbbb4cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
    Prediction(
        id="6",
        pair="BNB/USDT",
        timeframe="1h",
        prediction=True,
        stake=0.0500,
        trueval=True,
        timestamp=1701675800,
        source="kraken",
        payout=0.0500,
        slot=1701675900,
        user="0xbbbb4cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
    Prediction(
        id="7",
        pair="ETH/USDT",
        timeframe="1h",
        prediction=True,
        stake=None,
        trueval=False,
        timestamp=1701589400,
        source="binance",
        payout=0.0,
        slot=1701589500,
        user="0xcccc4cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
]


@enforce_types
def test_get_traction_statistics():
    predictions = sample_predictions + extra_predictions
    stats_df = get_traction_statistics(predictions)
    assert isinstance(stats_df, pl.DataFrame)
    assert stats_df.shape == (3, 3)
    assert "datetime" in stats_df.columns
    assert "daily_unique_predictoors_count" in stats_df.columns
    assert "cum_daily_unique_predictoors_count" in stats_df.columns
    assert stats_df["cum_daily_unique_predictoors_count"].to_list() == [2, 3, 3]


@enforce_types
def test_get_slot_statistics():
    predictions = sample_predictions + extra_predictions
    stats_df = get_slot_statistics(predictions)
    assert isinstance(stats_df, pl.DataFrame)
    assert stats_df.shape == (6, 8)
    assert "datetime" in stats_df.columns
    assert "pair" in stats_df.columns
    assert "timeframe" in stats_df.columns
    assert "slot" in stats_df.columns
    assert "n_predictoors" in stats_df.columns
    assert "sum_stake" in stats_df.columns
    assert "sum_payout" in stats_df.columns
    # 3rd is id = "7" > stake = None
    # 4th is id = "2" + "5" > stake = 0.05 + 0.05 = 0.1
    assert stats_df["sum_payout"].to_list() == [0.0, 0.05, 0.05, 0.0, 0.0, 0.05]
    assert stats_df["sum_stake"].to_list() == [0.05, 0.1, 0.05, 0.05, 0.0, 0.05]
