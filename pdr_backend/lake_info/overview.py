import logging
from typing import Dict, List

import polars as pl
from enforce_typing import enforce_types
from polars.dataframe.frame import DataFrame

from pdr_backend.lake.table import Table
from pdr_backend.lake.payout import Payout
from pdr_backend.lake.table_bronze_pdr_predictions import BronzePrediction

pl.Config.set_tbl_hide_dataframe_shape(True)

logger = logging.getLogger("LakeInfo")


class TableViewsOverview:
    def __init__(self, db):
        self.db = db

        self.all_table_names = self.db.get_table_names(all_schemas=True)
        self.all_view_names = self.db.get_view_names()
        self.table_info: Dict[str, DataFrame] = {}
        self.view_info: Dict[str, DataFrame] = {}

        for table_name in self.all_table_names:
            self.table_info[table_name] = self.db.query_data(
                "SELECT * FROM {}".format(table_name)
            )

        for view_name in self.all_view_names:
            self.view_info[view_name] = self.db.query_data(
                "SELECT * FROM {}".format(view_name)
            )

    def get_filtered_result(self, table_name: str, filter_value: str) -> DataFrame:
        return self.db.query_data(
            "SELECT * FROM {} WHERE user = '{}' LIMIT 100".format(
                table_name, filter_value
            )
        )


class ValidationOverview:
    def __init__(self, db):
        self.db = db

        self.all_table_names = self.db.get_table_names(all_schemas=True)
        self.all_view_names = self.db.get_view_names()

        self.validations = {
            "validate_tables_in_lake": self.validate_expected_table_names,
            "validate_no_views_in_lake": self.validate_expected_view_names,
            "validate_no_gaps_in_bronze_predictions": self.validate_lake_bronze_predictions_gaps,
            "validate_no_duplicate_rows_in_lake": self.validate_lake_tables_no_duplicates,
            "validate_no_unmatched_payouts": self.validate_no_unmatched_payouts,
        }

        self.validation_results: Dict[str, List[str]] = {}
        for key, value in self.validations.items():
            result = value()
            self.validation_results[key] = result

    def validate_expected_table_names(self) -> List[str]:
        violations: List[str] = []
        expected_table_names = self.all_table_names

        temp_table_names = self.all_table_names

        for table_name in set(temp_table_names) - set(expected_table_names):
            violations.append(
                "Unexpected table in lake - [Table: {}]".format(table_name)
            )

        for table_name in set(expected_table_names) - set(temp_table_names):
            violations.append("Missing table in lake - [Table: {}]".format(table_name))

        return violations

    def validate_expected_view_names(self) -> List[str]:
        violations: List[str] = []
        violations = [
            "Unexpected view: {}. Please clean using CLI.".format(view_name)
            for view_name in self.all_view_names
        ]

        return violations

    @enforce_types
    def validate_lake_bronze_predictions_gaps(self) -> List[str]:
        """
        description:
            Validate that the [lake slots] data has very few timestamp gaps.
            Find distinct slots, such that we can get the
            timedelta between each slot -> last_slot.
            Aggregate the count of each timedelta
            Then calculate the percentage of the most common ones
            We can then log the others, or something similar to analyze elsewhere

        how to improve:
            Expand ohlcv into lake/this check
        """
        violations: List[str] = []
        table_name = BronzePrediction.get_lake_table_name()

        # Query retrieves results grouped by [pair, timeframe, slot]
        # We observe the timedelta between each slot group, equal to 300s or 3600s respectively
        # Finally, we only count each instance as 1 because it represents a grouping of events
        query = """
            WITH slots AS (
                SELECT
                    pair,
                    timeframe,
                    slot
                FROM pdr_predictions
                GROUP BY pair, timeframe, slot
                ORDER BY pair, timeframe, slot
            ),
            lag_slots AS (
                SELECT
                    pair,
                    timeframe,
                    slot,
                    slot - LAG(slot, 1) OVER (
                      PARTITION BY pair, timeframe ORDER BY slot) as timedelta
                FROM slots
            ),
            data AS (
                SELECT
                    pair,
                    timeframe,
                    slot,
                    strftime(TO_TIMESTAMP(slot), '%d-%m-%Y %H:%M') AS datetime,
                    COUNT(*) as count
                FROM pdr_predictions
                GROUP BY pair, timeframe, slot
            )
            SELECT
                data.pair,
                data.timeframe,
                data.slot,
                data.datetime,
                lag_slots.timedelta,
                1 as count
            FROM data
            JOIN lag_slots
            ON data.slot = lag_slots.slot
            AND data.pair = lag_slots.pair
            AND data.timeframe = lag_slots.timeframe
            ORDER BY data.pair, data.timeframe, data.slot
        """

        # Process query and get results
        query = query.format(table_name)
        df: pl.DataFrame = self.db.query_data(query)

        # Get the count of slots with the same timedelta
        # understand how frequent the event/slots are happening based
        counts_per_timedelta = (
            df.group_by(["pair", "timeframe", "timedelta"])
            .agg([pl.col("count").sum().alias("total_count")])
            .drop_nulls()
            .sort(["pair", "timeframe", "timedelta"])
        )

        # Quality of Gap in data
        # 99.5% of the data should be without gaps
        alert_threshold = 99.5
        gap_pct = (
            (
                counts_per_timedelta.group_by(["pair", "timeframe"])
                .agg([(pl.sum("total_count").alias("sum_total_count"))])
                .join(
                    counts_per_timedelta,
                    on=["pair", "timeframe"],
                    how="left",
                    coalesce=True,
                )
                .with_columns(
                    [
                        (pl.col("total_count") / pl.col("sum_total_count") * 100).alias(
                            "gap_pct"
                        ),
                        (
                            pl.col("total_count") / pl.col("sum_total_count") * 100
                            < alert_threshold
                        ).alias("alert"),
                    ]
                )
            )
            .filter((pl.col("timedelta") == 300) | (pl.col("timedelta") == 3600))
            .sort(["pair", "timeframe", "timedelta"])
        )

        # check if quality is less than 99.5
        gap_validation_failures = gap_pct.filter(pl.col("gap_pct") < alert_threshold)

        if gap_validation_failures.shape[0] == 0:
            logger.info("No gaps found in bronze_predictions.")
            return violations

        # Report results
        logger.info("[Gap Validation - %s Table]", table_name)
        logger.info("[%s] feeds in gap validation", gap_pct.shape[0])

        # display report in a readable format
        logger.info(
            "[%s] feeds failed gap validation", gap_validation_failures.shape[0]
        )
        with pl.Config(tbl_rows=100):
            logger.info("%s Gap Report\n%s", table_name, gap_pct)

        violations.append("Gap validation failed. Please review logs.")

        return violations

    @enforce_types
    def validate_lake_tables_no_duplicates(self) -> List[str]:
        """
        description:
            Validate that there are no duplicate rows in the lake tables using a single column
            For every duplicate in a table log 1 row w/: table_name, id, date, count_duplicates

            This function logs a table with the following columns:
            - table_name, count_duplicates

            You can call write_csv(validate_no_duplicats.csv) to get a report.
        """
        violations = []
        duplicate_summary = pl.DataFrame()
        duplicate_rows = pl.DataFrame()

        # get duplicate incidents
        query_duplicate_summary = """
            SELECT
                'target_table' as table_name,
                COUNT(*) as incident_count
            FROM (
                SELECT
                    ID as ID,
                    timestamp,
                FROM target_table
                GROUP BY ID, timestamp
                HAVING COUNT(*) > 1
            ) as inner_query
            GROUP BY table_name
        """

        for table_name in self.all_table_names:
            query = query_duplicate_summary.replace("target_table", table_name)
            summary_df: pl.DataFrame = self.db.query_data(query)

            if summary_df.shape[0] > 0:
                # get individual instances of duplicate rows
                query_duplicate_rows = """
                    SELECT
                        'target_table' as table_name,
                        known_duplicates.ID,
                        known_duplicates.timestamp
                    FROM (
                        SELECT
                            ID as ID,
                            timestamp,
                        FROM target_table
                        GROUP BY ID, timestamp
                        HAVING COUNT(*) > 1
                    ) as known_duplicates
                    GROUP BY table_name, ID, timestamp
                """

                query = query_duplicate_rows.replace("target_table", table_name)
                rows_df: pl.DataFrame = self.db.query_data(query)
                duplicate_rows = (
                    duplicate_rows.vstack(rows_df)
                    if duplicate_rows.shape[0] > 0
                    else rows_df
                )

                duplicate_summary = (
                    duplicate_summary.vstack(summary_df)
                    if duplicate_summary.shape[0] > 0
                    else summary_df
                )
                violations.append(f"Table {table_name} has duplicates.")

        if duplicate_summary.shape[0] == 0:
            logger.info("No duplicate rows found in the lake.")
            return violations

        logger.info("Duplicate Summary\n%s", duplicate_summary)
        logger.info("Duplicate Rows:\n%s", duplicate_rows)

        # to write out and debug:
        duplicate_rows.write_csv("validate_duplicate_rows.csv")

        return violations

    @enforce_types
    def validate_no_unmatched_payouts(self) -> List[str]:
        """
        @description
            validates that all payouts have been able to match with a prediction
        """
        violations: list[str] = []

        # get all payouts
        # we want to select all payouts
        # we want to then join with predictions, and then filter for unmatched payouts
        # as long as their timestamp is within first/last prediction['timestamp] rows
        query_unmatched_payouts = f"""
            WITH payouts AS (
                SELECT
                    ID,
                    timestamp
                FROM {Table.from_dataclass(Payout).table_name}
            ), bronze_predictions AS (
                SELECT
                    ID,
                    timestamp,
                    max(timestamp) as max_timestamp,
                    min(timestamp) as min_timestamp
                FROM {Table.from_dataclass(BronzePrediction).table_name}
                GROUP BY ID, timestamp
            ),
            unmatched_payouts AS (
                SELECT
                    payouts.ID,
                    payouts.timestamp
                FROM payouts
                LEFT JOIN bronze_predictions
                ON payouts.ID = bronze_predictions.ID
                WHERE bronze_predictions.ID IS NULL
                AND payouts.timestamp BETWEEN bronze_predictions.min_timestamp AND bronze_predictions.max_timestamp
            )
            select * from unmatched_payouts;
        """

        rows_df: pl.DataFrame = self.db.query_data(query_unmatched_payouts)

        if rows_df is None or rows_df.shape[0] == 0:
            logger.info("No unmatched payouts found in the lake.")
            return violations

        violations.append(f"Unmatched Payouts:\n{rows_df}")
        return violations
