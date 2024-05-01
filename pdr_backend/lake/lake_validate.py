from typing import Dict, List
from enforce_typing import enforce_types

import polars as pl
from polars.dataframe.frame import DataFrame

from pdr_backend.lake.csv_data_store import CSVDataStore
from pdr_backend.lake.persistent_data_store import PersistentDataStore
from pdr_backend.lake.table_bronze_pdr_predictions import bronze_pdr_predictions_table_name
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.lake.lake_info import LakeInfo

from pdr_backend.lake.gql_data_factory import GQLDataFactory
from pdr_backend.lake.etl import ETL

pl.Config.set_tbl_hide_dataframe_shape(True)


@enforce_types
class LakeValidate(LakeInfo):
    def __init__(self, ppss: PPSS):
        super().__init__(ppss)
        
        self.config = {
            "Validate table names in lake match expected values.": self.validate_expected_table_names,
            "Validate no views in lake.": self.validate_expected_view_names,
            "Validate few gaps in bronze_predictions.": self.validate_lake_bronze_predictions_gaps,
        }
        self.results: Dict[str, (str, bool)] = {}

        self.csvds = CSVDataStore(ppss.lake_ss.lake_dir)
        self.gql_data_factory = GQLDataFactory(ppss)
        self.etl = ETL(ppss, self.gql_data_factory)


    @enforce_types
    def validate_expected_table_names(self) -> (bool, str):
        # test result and return message
        expected_table_names = [
            self.etl.raw_table_names,
            self.etl.bronze_table_names,
        ]

        if self.all_table_names == expected_table_names:
            return (True, "Tables in lake match expected Complete-ETL table names.")
        
        return (False, "Tables in lake [{}], do not match expected Complete-ETL table names [{}]".format(self.all_table_names, expected_table_names))
    

    @enforce_types
    def validate_expected_view_names(self) -> (bool, str):
        if len(self.all_view_names) == 0:
            return (True, "Clean Lake contains no VIEWs.")
        return (False,"Lake contains VIEWs. Please review logs and clean lake using the CLI.")
    

    @enforce_types
    def validate_lake_bronze_predictions_gaps(self) -> (bool, str):
        """
        description:
            Validate that the [lake slots] data has very few timestamp gaps.
            Find distinct slots, such that we can get the timedelta between each slot -> last_slot.
            We're goiing to aggregate the count of each timedelta, and then calculate the percentage of the most common ones
            We can then log the others, or something similar to analyze elsewhere

        how to improve:
            Expand ohlcv into lake/this check
        """
        table_name = bronze_pdr_predictions_table_name
        
        # Query retrieves results grouped by [pair, timeframe, slot]
        # We first observe the timedelta between each slot group, which should equal 300s or 3600s respectively
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
        # pair,timeframe,timedelta,total_count
        # ADA/USDT,5m,,1
        # ADA/USDT,5m,300,8314
        # ADA/USDT,5m,3900,1
        counts_per_timedelta = df.groupby(['pair','timeframe','timedelta']).agg([
            pl.col('count').sum().alias('total_count')
        ]).sort(['pair','timeframe','timedelta'])

        # Quality of Gap in data
        # we want to calculate the total_count / sum(total_count for that pair,timeframe) * 100
        # this should give us an idea regarding the gappiness and quality of the data
        # pair,timeframe,sum_total_count,timedelta,total_count,gap_pct
        # ADA/USDT,1h,6,3600,5,83.33333333333334
        # ADA/USDT,5m,8316,300,8314,99.97594997594997
        gap_pct = (
            counts_per_timedelta
            .groupby(['pair', 'timeframe'])
            .agg([
                (pl.sum("total_count").alias("sum_total_count"))
            ])
            .join(
                counts_per_timedelta,
                on=['pair', 'timeframe'],
                how='left'
            )
            .with_columns([
                (pl.col("total_count") / pl.col("sum_total_count") * 100).alias("gap_pct")
            ])
        ).filter(
            (pl.col('timedelta') == 300) | (pl.col('timedelta') == 3600)
        ).sort(['pair','timeframe','timedelta'])

        # Provide report on all tables if quality is less than 99.5
        alert_threshold = 99.5
        gap_validation_failures = gap_pct.filter(pl.col('gap_pct') < alert_threshold)
        
        print(">>> {} [{}] items in the gap_pct validation".format(table_name, gap_pct.shape[0]))
        print(">>> {} [{}] items failed the gap_pct validation".format(table_name, gap_validation_failures.shape[0]))
            
        if gap_validation_failures.shape[0] > 0:
            print(">>> {} gap_pct report: [{}]".format(table_name, gap_pct))
            return (False,"Gap Validation - Gaps detected in lake data. Please review logs.")
            
        return (True, "Gap Validation - More than 99.5% of data doesn't have gaps")
        

    def generate(self):
        super().generate()

        for key, value in self.config.items():
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
        print("\nValidation Results:")
        num_errors = len([result for result in self.results.values() if not result[0]])
        num_successes = len([result for result in self.results.values() if result[0]])
        total = len(self.results)

        for key, (success, message) in self.results.items():
            print(f"{key}: {success} - {message}")
            
        print(f"\nErrors: {num_errors}, Successes: {num_successes}, Total: {total}")

        
    @enforce_types
    def print_table_info(self, source: Dict[str, DataFrame]):
        super().print_table_info(source)
        self.print_results()


    @enforce_types
    def run(self):
        super().run()