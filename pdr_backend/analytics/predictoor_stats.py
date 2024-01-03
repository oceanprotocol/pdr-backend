import os
from typing import Dict, List, Set, Tuple, TypedDict

import matplotlib.pyplot as plt
import polars as pl
from enforce_typing import enforce_types

from pdr_backend.contract.prediction import Prediction
from pdr_backend.util.csvs import get_plots_dir


class PairTimeframeStat(TypedDict):
    pair: str
    timeframe: str
    accuracy: float
    stake: float
    payout: float
    number_of_predictions: int


class PredictoorStat(TypedDict):
    predictoor_address: str
    accuracy: float
    stake: float
    payout: float
    number_of_predictions: int
    details: Set[Tuple[str, str, str]]


@enforce_types
def aggregate_prediction_statistics(
    all_predictions: List[Prediction],
) -> Tuple[Dict[str, Dict], int]:
    """
    Aggregates statistics from a list of prediction objects. It organizes statistics
    by currency pair and timeframe and predictor address. For each category, it
    tallies the total number of predictions, the number of correct predictions,
    and the total stakes and payouts. It also returns the total number of correct
    predictions across all categories.

    Args:
        all_predictions (List[Prediction]): A list of Prediction objects to aggregate.

    Returns:
        Tuple[Dict[str, Dict], int]: A tuple containing a dictionary of aggregated
        statistics and the total number of correct predictions.
    """
    stats: Dict[str, Dict] = {"pair_timeframe": {}, "predictor": {}}
    correct_predictions = 0

    for prediction in all_predictions:
        pair_timeframe_key = (prediction.pair, prediction.timeframe)
        predictor_key = prediction.user
        source = prediction.source

        is_correct = prediction.prediction == prediction.trueval

        if pair_timeframe_key not in stats["pair_timeframe"]:
            stats["pair_timeframe"][pair_timeframe_key] = {
                "correct": 0,
                "total": 0,
                "stake": 0,
                "payout": 0.0,
            }

        if predictor_key not in stats["predictor"]:
            stats["predictor"][predictor_key] = {
                "correct": 0,
                "total": 0,
                "stake": 0,
                "payout": 0.0,
                "details": set(),
            }

        if is_correct:
            correct_predictions += 1
            stats["pair_timeframe"][pair_timeframe_key]["correct"] += 1
            stats["predictor"][predictor_key]["correct"] += 1

        stats["pair_timeframe"][pair_timeframe_key]["total"] += 1
        stats["pair_timeframe"][pair_timeframe_key]["stake"] += prediction.stake
        stats["pair_timeframe"][pair_timeframe_key]["payout"] += prediction.payout

        stats["predictor"][predictor_key]["total"] += 1
        stats["predictor"][predictor_key]["stake"] += prediction.stake
        stats["predictor"][predictor_key]["payout"] += prediction.payout
        stats["predictor"][predictor_key]["details"].add(
            (prediction.pair, prediction.timeframe, source)
        )

    return stats, correct_predictions


@enforce_types
def get_endpoint_statistics(
    all_predictions: List[Prediction],
) -> Tuple[float, List[PairTimeframeStat], List[PredictoorStat]]:
    """
    Calculates the overall accuracy of predictions, and aggregates detailed prediction
    statistics by currency pair and timeframe with predictoor.

    The function first determines the overall accuracy of all given predictions.
    It then organizes individual prediction statistics into two separate lists:
    one for currency pair and timeframe statistics, and another for predictor statistics.

    Args:
        all_predictions (List[Prediction]): A list of Prediction objects to be analyzed.

    Returns:
        Tuple[float, List[Dict[str, Any]], List[Dict[str, Any]]]: A tuple containing the
        overall accuracy as a float, a list of dictionaries with statistics for each
        currency pair and timeframe, and a list of dictionaries with statistics for each
        predictor.
    """
    total_predictions = len(all_predictions)
    stats, correct_predictions = aggregate_prediction_statistics(all_predictions)

    overall_accuracy = (
        correct_predictions / total_predictions * 100 if total_predictions else 0
    )

    pair_timeframe_stats: List[PairTimeframeStat] = []
    for key, stat_pair_timeframe_item in stats["pair_timeframe"].items():
        pair, timeframe = key
        accuracy = (
            stat_pair_timeframe_item["correct"]
            / stat_pair_timeframe_item["total"]
            * 100
            if stat_pair_timeframe_item["total"]
            else 0
        )
        pair_timeframe_stat: PairTimeframeStat = {
            "pair": pair,
            "timeframe": timeframe,
            "accuracy": accuracy,
            "stake": stat_pair_timeframe_item["stake"],
            "payout": stat_pair_timeframe_item["payout"],
            "number_of_predictions": stat_pair_timeframe_item["total"],
        }
        pair_timeframe_stats.append(pair_timeframe_stat)

    predictoor_stats: List[PredictoorStat] = []
    for predictoor_addr, stat_predictoor_item in stats["predictor"].items():
        accuracy = (
            stat_predictoor_item["correct"] / stat_predictoor_item["total"] * 100
            if stat_predictoor_item["total"]
            else 0
        )
        predictoor_stat: PredictoorStat = {
            "predictoor_address": predictoor_addr,
            "accuracy": accuracy,
            "stake": stat_predictoor_item["stake"],
            "payout": stat_predictoor_item["payout"],
            "number_of_predictions": stat_predictoor_item["total"],
            "details": set(stat_predictoor_item["details"]),
        }
        predictoor_stats.append(predictoor_stat)

    return overall_accuracy, pair_timeframe_stats, predictoor_stats


@enforce_types
def get_cli_statistics(all_predictions: List[Prediction]) -> None:
    total_predictions = len(all_predictions)

    stats, correct_predictions = aggregate_prediction_statistics(all_predictions)

    if total_predictions == 0:
        print("No predictions found.")
        return

    if correct_predictions == 0:
        print("No correct predictions found.")
        return

    print(f"Overall Accuracy: {correct_predictions/total_predictions*100:.2f}%")

    for key, stat_pair_timeframe_item in stats["pair_timeframe"].items():
        pair, timeframe = key
        accuracy = (
            stat_pair_timeframe_item["correct"]
            / stat_pair_timeframe_item["total"]
            * 100
        )
        print(f"Accuracy for Pair: {pair}, Timeframe: {timeframe}: {accuracy:.2f}%")
        print(f"Total stake: {stat_pair_timeframe_item['stake']}")
        print(f"Total payout: {stat_pair_timeframe_item['payout']}")
        print(f"Number of predictions: {stat_pair_timeframe_item['total']}\n")

    for predictoor_addr, stat_predictoor_item in stats["predictor"].items():
        accuracy = stat_predictoor_item["correct"] / stat_predictoor_item["total"] * 100
        print(f"Accuracy for Predictoor Address: {predictoor_addr}: {accuracy:.2f}%")
        print(f"Stake: {stat_predictoor_item['stake']}")
        print(f"Payout: {stat_predictoor_item['payout']}")
        print(f"Number of predictions: {stat_predictoor_item['total']}")
        print("Details of Predictions:")
        for detail in stat_predictoor_item["details"]:
            print(f"Pair: {detail[0]}, Timeframe: {detail[1]}, Source: {detail[2]}")
        print("\n")


@enforce_types
def get_traction_statistics(preds_df: pl.DataFrame) -> pl.DataFrame:
    # Calculate predictoor traction statistics
    # Predictoor addresses are aggregated historically
    stats_df = (
        preds_df.with_columns(
            [
                # use strftime(%Y-%m-%d %H:00:00) to get hourly intervals
                pl.from_epoch("timestamp", time_unit="s")
                .dt.strftime("%Y-%m-%d")
                .alias("datetime"),
            ]
        )
        .group_by("datetime")
        .agg(
            [
                pl.col("user").unique().alias("daily_unique_predictoors"),
                pl.col("user").unique().count().alias("daily_unique_predictoors_count"),
                pl.lit(1).alias("index"),
            ]
        )
        .sort("datetime")
        .with_columns(
            [
                pl.col("daily_unique_predictoors")
                .cumulative_eval(pl.element().explode().unique().count())
                .over("index")
                .alias("cum_daily_unique_predictoors_count")
            ]
        )
        .select(
            [
                "datetime",
                "daily_unique_predictoors_count",
                "cum_daily_unique_predictoors_count",
            ]
        )
    )

    return stats_df


@enforce_types
def plot_traction_daily_statistics(stats_df: pl.DataFrame, pq_dir: str) -> None:
    assert "datetime" in stats_df.columns
    assert "daily_unique_predictoors_count" in stats_df.columns

    charts_dir = get_plots_dir(pq_dir)

    dates = stats_df["datetime"].to_list()
    ticks = int(len(dates) / 5) if len(dates) > 5 else 2

    # draw unique_predictoors
    chart_path = os.path.join(charts_dir, "daily_unique_predictoors.png")
    plt.figure(figsize=(10, 6))
    plt.plot(
        stats_df["datetime"].to_pandas(),
        stats_df["daily_unique_predictoors_count"],
        marker="o",
        linestyle="-",
    )
    plt.xlabel("Date")
    plt.ylabel("# Unique Predictoor Addresses")
    plt.title("Daily # Unique Predictoor Addresses")
    plt.xticks(range(0, len(dates), ticks), dates[::ticks], rotation=90)
    plt.tight_layout()
    plt.savefig(chart_path)
    plt.close()
    print("Chart created:", chart_path)


@enforce_types
def plot_traction_cum_sum_statistics(stats_df: pl.DataFrame, pq_dir: str) -> None:
    assert "datetime" in stats_df.columns
    assert "cum_daily_unique_predictoors_count" in stats_df.columns

    charts_dir = get_plots_dir(pq_dir)

    dates = stats_df["datetime"].to_list()
    ticks = int(len(dates) / 5) if len(dates) > 5 else 2

    # draw cum_unique_predictoors
    chart_path = os.path.join(charts_dir, "daily_cumulative_unique_predictoors.png")
    plt.figure(figsize=(10, 6))
    plt.plot(
        stats_df["datetime"].to_pandas(),
        stats_df["cum_daily_unique_predictoors_count"],
        marker="o",
        linestyle="-",
    )
    plt.xlabel("Date")
    plt.ylabel("# Unique Predictoor Addresses")
    plt.title("Cumulative # Unique Predictoor Addresses")
    plt.xticks(range(0, len(dates), ticks), dates[::ticks], rotation=90)
    plt.tight_layout()
    plt.savefig(chart_path)
    plt.close()
    print("Chart created:", chart_path)


@enforce_types
def get_slot_statistics(preds_df: pl.DataFrame) -> pl.DataFrame:
    # Create a <pair-timeframe-slot> key to group predictions
    slots_df = (
        preds_df.with_columns(
            [
                (pl.col("pair").cast(str) + "-" + pl.col("timeframe").cast(str)).alias(
                    "pair_timeframe"
                ),
                (
                    pl.col("pair").cast(str)
                    + "-"
                    + pl.col("timeframe").cast(str)
                    + "-"
                    + pl.col("slot").cast(str)
                ).alias("pair_timeframe_slot"),
            ]
        )
        .group_by("pair_timeframe_slot")
        .agg(
            [
                pl.col("pair").first(),
                pl.col("timeframe").first(),
                pl.col("slot").first(),
                pl.col("pair_timeframe").first(),
                # use strftime(%Y-%m-%d %H:00:00) to get hourly intervals
                pl.from_epoch("timestamp", time_unit="s")
                .first()
                .dt.strftime("%Y-%m-%d")
                .alias("datetime"),
                pl.col("user")
                .unique()
                .count()
                .alias("n_predictoors"),  # n unique predictoors
                pl.col("stake").min().alias("min_stake"),  # min stake
                pl.col("stake").max().alias("max_stake"),  # max stake
                pl.col("stake").mean().alias("mean_stake"),  # mean stake
                pl.col("stake").sum().alias("sum_stake"),  # Sum of slot stake
                pl.col("payout").min().alias("min_payout"),  # min payout
                pl.col("payout").max().alias("max_payout"),  # max payout
                pl.col("payout").mean().alias("mean_payout"),  # mean payout
                pl.col("payout").sum().alias("sum_payout"),  # Sum of slot payout
            ]
        )
        .sort(["pair", "timeframe", "slot"])
    )

    return slots_df


@enforce_types
def get_mean_slots_df(slots_df: pl.DataFrame) -> pl.DataFrame:
    return slots_df.select(
        [
            pl.col("pair_timeframe").first(),
            pl.col("datetime").first(),
            pl.col("sum_stake").mean().alias("mean_stake"),
            pl.col("sum_payout").mean().alias("mean_payout"),
            pl.col("n_predictoors").mean().alias("mean_n_predictoors"),
        ]
    )


@enforce_types
def calculate_slot_daily_statistics(
    slots_df: pl.DataFrame,
) -> pl.DataFrame:
    # for each <pair_timeframe,datetime> take a sample of up-to 5
    # then for each <pair_timeframe,datetime> calc daily mean_stake, mean_payout, ...
    # then for each <datetime> sum those numbers across all feeds
    slots_daily_df = (
        slots_df.group_by(["pair_timeframe", "datetime"])
        .map_groups(
            lambda df: get_mean_slots_df(df.sample(5))
            if len(df) > 5
            else get_mean_slots_df(df)
        )
        .group_by("datetime")
        .agg(
            [
                pl.col("mean_stake").sum().alias("daily_average_stake"),
                pl.col("mean_payout").sum().alias("daily_average_payout"),
                pl.col("mean_n_predictoors")
                .mean()
                .alias("daily_average_predictoor_count"),
            ]
        )
        .sort("datetime")
    )

    return slots_daily_df


@enforce_types
def plot_slot_daily_statistics(slots_df: pl.DataFrame, pq_dir: str) -> None:
    assert "pair_timeframe" in slots_df.columns
    assert "slot" in slots_df.columns
    assert "n_predictoors" in slots_df.columns

    # calculate slot daily statistics
    slots_daily_df = calculate_slot_daily_statistics(slots_df)

    charts_dir = get_plots_dir(pq_dir)

    dates = slots_daily_df["datetime"].to_list()
    ticks = int(len(dates) / 5) if len(dates) > 5 else 2

    # draw daily predictoor stake in $OCEAN
    chart_path = os.path.join(charts_dir, "daily_average_stake.png")
    plt.figure(figsize=(10, 6))
    plt.plot(
        slots_daily_df["datetime"].to_pandas(),
        slots_daily_df["daily_average_stake"],
        marker="o",
        linestyle="-",
    )
    plt.xlabel("Date")
    plt.ylabel("Average $OCEAN Staked")
    plt.title("Daily average $OCEAN staked per slot, across all Feeds")
    plt.xticks(range(0, len(dates), ticks), dates[::ticks], rotation=90)
    plt.tight_layout()
    plt.savefig(chart_path)
    plt.close()
    print("Chart created:", chart_path)

    # draw daily predictoor payouts in $OCEAN
    chart_path = os.path.join(charts_dir, "daily_slot_average_predictoors.png")
    plt.figure(figsize=(10, 6))
    plt.plot(
        slots_daily_df["datetime"].to_pandas(),
        slots_daily_df["daily_average_predictoor_count"],
        marker="o",
        linestyle="-",
    )
    plt.xlabel("Date")
    plt.ylabel("Average Predictoors")
    plt.title("Average # Predictoors competing per slot, per feed")
    plt.xticks(range(0, len(dates), ticks), dates[::ticks], rotation=90)
    plt.tight_layout()
    plt.savefig(chart_path)
    plt.close()
    print("Chart created:", chart_path)
