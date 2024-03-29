import logging
import os
from typing import Set, Tuple, TypedDict

import matplotlib.pyplot as plt
import polars as pl
from enforce_typing import enforce_types

from pdr_backend.util.csvs import get_plots_dir

logger = logging.getLogger("predictoor_stats")


class PairTimeframeStat(TypedDict):
    pair: str
    timeframe: str
    accuracy: float
    exchange: str
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
def get_feed_summary_stats(predictions_df: pl.DataFrame) -> pl.DataFrame:
    # 1 - filter from lake only the rows that you're looking for
    df = predictions_df.filter(
        ~((pl.col("trueval").is_null()) | (pl.col("payout").is_null()))
    )

    df = df.with_columns(pl.col("prediction").eq(pl.col("trueval")).cast(pl.UInt8).alias("is_correct"))
    # Group by pair
    df = df.group_by(["pair", "timeframe"]).agg(
        pl.col("source").first().alias("source"),
        pl.col("payout").sum().alias("sum_payout"),
        pl.col("stake").sum().alias("sum_stake"),
        pl.col("prediction").count().alias("num_predictions"),
        (pl.col("is_correct").sum() / pl.col("pair").count() * 100).alias("accuracy"),
    )

    return df


@enforce_types
def get_predictoor_summary_stats(predictions_df: pl.DataFrame) -> pl.DataFrame:
    # 1 - filter from lake only the rows that you're looking for
    df = predictions_df.filter(
        ~((pl.col("trueval").is_null()) | (pl.col("payout").is_null()))
    )

    df = df.with_columns(pl.col("prediction").eq(pl.col("trueval")).cast(pl.UInt8).alias("is_correct"))
    # Group by pair
    df = df.group_by(["user", "pair", "timeframe"]).agg(
        pl.col("source").first().alias("source"),
        pl.col("payout").sum().alias("sum_payout"),
        pl.col("stake").sum().alias("sum_stake"),
        pl.col("prediction").count().alias("num_predictions"),
        (pl.col("is_correct").sum() / pl.col("pair").count() * 100).alias("accuracy"),
    )

    return df


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
    logger.info("Chart created: %s", chart_path)


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
    logger.info("Chart created: %s", chart_path)


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
                pl.col("payout").sum().alias("slot_payout"),  # Sum of slot payout
                pl.col("stake").sum().alias("slot_stake"),  # Sum of slot stake
            ]
        )
        .sort(["pair", "timeframe", "slot"])
    )

    return slots_df


def calculate_slot_daily_statistics(
    slots_df: pl.DataFrame,
) -> pl.DataFrame:
    def get_mean_slots_slots_df(slots_df: pl.DataFrame) -> pl.DataFrame:
        return slots_df.select(
            [
                pl.col("pair_timeframe").first(),
                pl.col("datetime").first(),
                pl.col("slot_stake").mean().alias("mean_stake"),
                pl.col("slot_payout").mean().alias("mean_payout"),
                pl.col("n_predictoors").mean().alias("mean_n_predictoors"),
            ]
        )

    # for each <pair_timeframe,datetime> take a sample of up-to 5
    # then for each <pair_timeframe,datetime> calc daily mean_stake, mean_payout, ...
    # then for each <datetime> sum those numbers across all feeds
    slots_daily_df = (
        slots_df.with_columns(
            pl.concat_str(["pair_timeframe", "datetime"]).alias("group_key")
        )
        .group_by("group_key")
        .map_groups(
            lambda df: (
                get_mean_slots_slots_df(df.sample(5))
                if len(df) > 5
                else get_mean_slots_slots_df(df)
            )
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
    logger.info("Chart created: %s", chart_path)

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
    logger.info("Chart created: %s", chart_path)
