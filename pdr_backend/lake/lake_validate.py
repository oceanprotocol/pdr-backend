from typing import Dict, List

import polars as pl
from polars.dataframe.frame import DataFrame

from pdr_backend.lake.persistent_data_store import PersistentDataStore
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.lake.lake_info import LakeInfo

pl.Config.set_tbl_hide_dataframe_shape(True)


class LakeValidate(LakeInfo):
    def __init__(self, ppss: PPSS):
        super().__init__(ppss)
        
    def generate(self):
        super().generate()

    def print_table_info(self, source: Dict[str, DataFrame]):
        super().print_table_info(source)

    def run(self):
        super().run()
