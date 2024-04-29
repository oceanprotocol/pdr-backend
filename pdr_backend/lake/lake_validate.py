from typing import Dict, List
from enforce_typing import enforce_types

import polars as pl
from polars.dataframe.frame import DataFrame

from pdr_backend.lake.persistent_data_store import PersistentDataStore
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.lake.lake_info import LakeInfo

from pdr_backend.lake.etl import ETL

pl.Config.set_tbl_hide_dataframe_shape(True)


@enforce_types
class LakeValidate(LakeInfo):
    def __init__(self, ppss: PPSS):
        super().__init__(ppss)
        
        self.config = {
            "Validate table names in lake match expected values.": self.validate_expected_table_names,
            "Validate view names in lake match expected values.": self.validate_expected_view_names,
            "Validate lake timestamp gaps.": self.validate_lake_timestamp_gaps,
        }
        self.results: Dict[str, (str, bool)] = {}


    @enforce_types
    def validate_expected_table_names(self) -> (bool, str):
        # test result and return message
        expected_table_names = [
            ETL.raw_table_names,
            ETL.bronze_table_names,
        ]

        if self.all_table_names == expected_table_names:
            return (True, "Tables in lake match expected Complete-ETL table names.")
        
        return (False, "Tables in lake [{}], do not match expected Complete-ETL table names [{}]".format(self.all_table_names, expected_table_names))
    

    @enforce_types
    def validate_expected_temp_names(self) -> (bool, str):
        if len(self.all_temp_names) == 0:
            return (True, "Clean Lake contains no TEMP tables.")
        return (False,"Lake contains TEMP tables. Please review logs and clean lake using the CLI.")
    

    @enforce_types
    def validate_lake_timestamp_gaps(self) -> (bool, str):
        """
        description:
            Validate that the [lake slots] data does not have any timestamp gaps, and other basic timestamp checks.
            Break tables down into chunks, and check for gaps between chunks using polars.
            Get the st and end timestamps, and chunk if needed.
            Do a random sampling of row chunks to check for gaps, such that you can iterate through the whole db.

        how to improve:
            Expand ohlcv into lake/this check
        """
        gap_errors = []

        # for table_name in self.all_table_names:
        #     df = self.pds.query
        #     df.select(pl.col("timestamp").diff().slice(1).rle()).unnest("timestamp").rename({"lengths":"seq_lengths", "values": "time_difference"})
        
        if len(gap_errors) == 0:
            return (True, "No gap errors. Data is perfect.")
        return (False,"Gaps detected in lake data. Please review logs and consider a lake resync.")


    def generate(self):
        super().generate()

        for key, value in self.config.items():
            result = self.validations[key] = value(self)
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