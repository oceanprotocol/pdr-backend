from typing import Dict, List
from enforce_typing import enforce_types

import polars as pl
from polars.dataframe.frame import DataFrame

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
            Validate that the [lake slots] data does not have any timestamp gaps, and other basic timestamp checks.
            Break tables down into chunks, and check for gaps between chunks using polars.
            Get the st and end timestamps, and chunk if needed.
            Do a random sampling of row chunks to check for gaps, such that you can iterate through the whole db.

        how to improve:
            Expand ohlcv into lake/this check
        """
        gap_errors = Dict[str, List[str]] = {}

        table_name = bronze_pdr_predictions_table_name
        timeframes = ["5m", "1h"]
        query = """
            select 
                slot,
                count(*) as predictions_count
            from {}
            where timeframe = {}
            group by slot
            order by slot
        """
        for timeframe in timeframes:
            query = query.format(table_name, timeframe)
            df = self.pds.query_data(query)
            print(">>> {} DF: [{}]".format(table_name, df))

            result = df.select(pl.col("slot").diff().slice(1).rle()) \
                .unnest("slot") \
                .rename({"lengths":"seq_lengths", "values": "time_difference"})

            print(">>> {} Data Gappiness: [{}]".format(table_name, result))
            if result['time_difference'].sum() > 0:
                print(">>> time difference sum > 0: ", result['time_difference'].sum())
                gap_errors[timeframe] = result

        if len(gap_errors) == 0:
            return (True, "No gap errors. Data is perfect.")
        
        return (False,"Gaps detected in lake data. Please review logs.")

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