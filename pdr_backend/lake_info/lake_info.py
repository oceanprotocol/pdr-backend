import logging
from typing import Dict, List

from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.lake.etl import ETL
from pdr_backend.lake.gql_data_factory import GQLDataFactory
from pdr_backend.lake_info.cli import CliRenderer
from pdr_backend.lake_info.html import HtmlRenderer
from pdr_backend.lake_info.overview import TableViewsOverview, ValidationOverview
from pdr_backend.ppss.ppss import PPSS

logger = logging.getLogger("LakeInfo")


# pylint: disable=too-many-instance-attributes
class LakeInfo:
    def __init__(self, ppss: PPSS, use_html: bool = False):
        self.db = DuckDBDataStore(ppss.lake_ss.lake_dir, read_only=True)
        self.gql_data_factory = GQLDataFactory(ppss)
        self.etl = ETL(ppss, self.gql_data_factory)

        self.html = use_html

    def run(self):
        if self.html:
            html_renderer = HtmlRenderer(self)
            html_renderer.show()
            return

        table_views_overview = TableViewsOverview(self.db)
        cli_renderer = CliRenderer(table_views_overview)
        cli_renderer.show()

    def run_validation(self):
        validation_overview = ValidationOverview(self.db)

        violations = [
            result
            for result in validation_overview.validation_results.values()
            if result is not None
        ]
        num_violations = 0

        for key, (violations) in validation_overview.validation_results.items():
            if violations is None or len(violations) == 0:
                print(f"[{key}] Validation Successful")
                continue

            print(f"[{key}] Validation Errors:")
            num_violations += len(violations)
            for violation in violations:
                print(f"> {violation}")

        print(f"Num violations: {num_violations}")
