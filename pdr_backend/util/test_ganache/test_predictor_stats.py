from typing import List, Set
from enforce_typing import enforce_types

from pdr_backend.util.predictoor_stats import (
    aggregate_prediction_statistics,
    get_endpoint_statistics,
    get_cli_statistics,
    get_system_statistics
)

from pdr_backend.util.subgraph_predictions import (
    Prediction,
)

import polars as pl

sample_predictions = [
    Prediction(
        pair="ADA/USDT",
        timeframe="5m",
        prediction=True,
        stake=0.050051425480971974,
        trueval=False,
        timestamp=1698527100,
        source="binance",
        payout=0.0,
        user="0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
    Prediction(
        pair="ADA/USDT",
        timeframe="5m",
        prediction=True,
        stake=0.0500,
        trueval=True,
        timestamp=1698527700,
        source="binance",
        payout=0.0,
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


multi_predictions = [
    Prediction(
        pair="ADA/USDT",
        timeframe="5m",
        prediction=True,
        stake=0.0500,
        trueval=False,
        timestamp=1701503100,
        source="binance",
        payout=0.0,
        user="0xaaaa4cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
    Prediction(
        pair="BTC/USDT",
        timeframe="5m",
        prediction=True,
        stake=0.0500,
        trueval=True,
        timestamp=1701589500,
        source="binance",
        payout=0.0,
        user="0xaaaa4cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
    Prediction(
        pair="ETH/USDT",
        timeframe="5m",
        prediction=True,
        stake=0.0500,
        trueval=True,
        timestamp=1701675900,
        source="binance",
        payout=0.0,
        user="0xaaaa4cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
    Prediction(
        pair="BTC/USDT",
        timeframe="1h",
        prediction=True,
        stake=0.0500,
        trueval=False,
        timestamp=1701503100,
        source="binance",
        payout=0.0,
        user="0xbbbb4cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
    Prediction(
        pair="XRP/USDT",
        timeframe="5m",
        prediction=True,
        stake=0.0500,
        trueval=True,
        timestamp=1701589500,
        source="binance",
        payout=0.0,
        user="0xbbbb4cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
    Prediction(
        pair="BNB/USDT",
        timeframe="1h",
        prediction=True,
        stake=0.0500,
        trueval=True,
        timestamp=1701675900,
        source="kraken",
        payout=0.0,
        user="0xbbbb4cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
    Prediction(
        pair="ETH/USDT",
        timeframe="1h",
        prediction=True,
        stake=None,
        trueval=False,
        timestamp=1701589500,
        source="binance",
        payout=0.0,
        user="0xcccc4cb4ff2584bad80ff5f109034a891c3d88dd",
    )
]


@enforce_types
def test_get_system_statistics():
    stats_df = get_system_statistics(multi_predictions)
    assert isinstance(stats_df, pl.DataFrame)
    assert stats_df.shape == (3, 3)
    assert "datetime" in stats_df.columns
    assert "cum_sum_stake" in stats_df.columns
    assert "cum_unique_predictoors" in stats_df.columns
    assert stats_df["cum_sum_stake"].round(2).to_list() == [0.1, 0.2, 0.3]

