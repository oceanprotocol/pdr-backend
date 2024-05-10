import logging
from typing import Dict, List
from enforce_typing import enforce_types

import polars as pl

from pdr_backend.lake.csv_data_store import CSVDataStore
from pdr_backend.lake.table_bronze_pdr_predictions import (
    bronze_pdr_predictions_table_name,
)
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.lake.lake_info import LakeInfo

from pdr_backend.lake.gql_data_factory import GQLDataFactory
from pdr_backend.lake.etl import ETL

pl.Config.set_tbl_hide_dataframe_shape(True)

logger = logging.getLogger("LakeValidate")


@enforce_types
class LakeValidate(LakeInfo):
    def __init__(self, ppss: PPSS):
        super().__init__(ppss)

        self.validations = {
            "validate_tables_in_lake": self.validate_expected_table_names,
            "validate_no_views_in_lake": self.validate_expected_view_names,
            "validate_no_gaps_in_bronze_predictions": self.validate_lake_bronze_predictions_gaps,
        }
        self.results: Dict[str, List[str]] = {}

        self.csvds = CSVDataStore(ppss.lake_ss.lake_dir)
        self.gql_data_factory = GQLDataFactory(ppss)
        self.etl = ETL(ppss, self.gql_data_factory)

    @enforce_types
    def validate_expected_table_names(self) -> List[str]:
        violations = []
        expected_table_names = []
        expected_table_names += self.etl.raw_table_names
        expected_table_names += self.etl.bronze_table_names
        expected_table_names.sort()

        temp_table_names = self.all_table_names
        temp_table_names.sort()

        if temp_table_names != expected_table_names:
            violations.append(
                "Tables in lake do not match expected names - [Lake: {}], [Expected: {}]".format(
                    temp_table_names, expected_table_names
                )
            )

        return violations

    @enforce_types
    def validate_expected_view_names(self) -> List[str]:
        violations = []
        if len(self.all_view_names) > 0:
            violations.append("Lake has VIEWs. Please clean lake using CLI.")

        return violations

    @enforce_types
    def validate_lake_bronze_predictions_gaps(self) -> List[str]:
        """
        description:
            Validate that the [lake slots] data has very few timestamp gaps.
            Find distinct slots, such that we can get the timedelta between each slot -> last_slot.
            Aggregate the count of each timedelta
            Then calculate the percentage of the most common ones
            We can then log the others, or something similar to analyze elsewhere

        how to improve:
            Expand ohlcv into lake/this check
        """
        violations = []
        table_name = bronze_pdr_predictions_table_name

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
                    slot - LAG(slot, 1) OVER (PARTITION BY pair, timeframe ORDER BY slot) as timedelta
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
        df: pl.DataFrame = self.pds.query_data(query)

        # Get the count of slots with the same timedelta
        # understand how frequent the event/slots are happening based
        counts_per_timedelta = (
            df.group_by(["pair", "timeframe", "timedelta"])
            .agg([pl.col("count").sum().alias("total_count")])
            .sort(["pair", "timeframe", "timedelta"])
        )

        # Quality of Gap in data
        # 99.5% of the data should be without gaps
        alert_threshold = 99.5
        gap_pct = (
            (
                counts_per_timedelta.group_by(["pair", "timeframe"])
                .agg([(pl.sum("total_count").alias("sum_total_count"))])
                .join(counts_per_timedelta, on=["pair", "timeframe"], how="left")
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

        # Report results
        logger.info("[Gap Validation - %s Table]", table_name)
        logger.info("[%s] feeds in gap validation", gap_pct.shape[0])

        # check if quality is less than 99.5
        gap_validation_failures = gap_pct.filter(pl.col("gap_pct") < alert_threshold)
        if gap_validation_failures.shape[0] != 0:
            # display report in a readable format
            logger.info(
                "[%s] feeds failed gap validation", gap_validation_failures.shape[0]
            )
            with pl.Config(tbl_rows=100):
                logger.info("%s Gap Report\n%s", table_name, gap_pct)

            violations.append("Gap validation failed. Please review logs.")

        return violations

    def generate(self):
        super().generate()

        for key, value in self.validations.items():
            result = value()
            self.results[key] = result

    def print_results(self):
        """
        description:
            The print statement should be formatted as follows:
            # loop results
            #   print message with: (1) key, (2) error/success, (3) message
            # print num errors, num successes, and total
        """
        violations = [result for result in self.results.values() if not result is None]
        num_violations = 0

        for key, (violations) in self.results.items():
            if violations is None or len(violations) == 0:
                print(f"{key} Validation Successful")

            print(f"{key} Validation Errors")
            num_violations += len(violations)
            for violation in violations:
                print(f"> {violation}")

        print(f"Num violations: {num_violations}")

    @enforce_types
    def run(self):
        self.generate()
        self.print_results()
