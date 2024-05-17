from typing import Dict, List

import polars as pl
from polars.dataframe.frame import DataFrame

from pdr_backend.lake.etl import ETL
from pdr_backend.lake.gql_data_factory import GQLDataFactory
from pdr_backend.lake.persistent_data_store import PersistentDataStore
from pdr_backend.lake.renderers.cli import CliRenderer
from pdr_backend.lake.renderers.html import HtmlRenderer
from pdr_backend.ppss.ppss import PPSS

pl.Config.set_tbl_hide_dataframe_shape(True)


# pylint: disable=too-many-instance-attributes
class LakeInfo:
    def __init__(self, ppss: PPSS, use_html: bool = False):
        self.pds = PersistentDataStore(ppss.lake_ss.lake_dir, read_only=True)
        self.gql_data_factory = GQLDataFactory(ppss)
        self.etl = ETL(ppss, self.gql_data_factory)

        self.all_table_names: List[str] = []
        self.table_info: Dict[str, DataFrame] = {}
        self.all_view_names: List[str] = []
        self.view_info: Dict[str, DataFrame] = {}

        self.html = use_html

    def generate(self):
        self.all_table_names = self.pds.get_table_names(all_schemas=True)

        for table_name in self.all_table_names:
            self.table_info[table_name] = self.pds.query_data(
                "SELECT * FROM {}".format(table_name)
            )

        self.all_view_names = self.pds.get_view_names()

        for view_name in self.all_view_names:
            self.view_info[view_name] = self.pds.query_data(
                "SELECT * FROM {}".format(view_name)
            )

    def run(self):
        self.generate()

        if self.html:
            html_renderer = HtmlRenderer(self)
            html_renderer.show()
            return

        cli_renderer = CliRenderer(self)
        cli_renderer.show()

    def validate_expected_table_names(self) -> List[str]:
        violations = []
        expected_table_names = self.etl.raw_table_names + self.etl.bronze_table_names

        temp_table_names = self.all_table_names

        for table_name in set(temp_table_names) - set(expected_table_names):
            violations.append(
                "Unexpected table in lake - [Table: {}]".format(table_name)
            )

        for table_name in set(expected_table_names) - set(temp_table_names):
            violations.append("Missing table in lake - [Table: {}]".format(table_name))

        return violations

    def validate_expected_view_names(self) -> List[str]:
        violations = []
        if len(self.all_view_names) > 0:
            violations.append("Lake has VIEWs. Please clean lake using CLI.")

        return violations
