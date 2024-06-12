from unittest.mock import Mock, patch

import polars as pl
import pytest
from enforce_typing import enforce_types

from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.lake.etl import (
    _ETL_REGISTERED_LAKE_TABLES,
    _ETL_REGISTERED_TABLE_NAMES,
    ETL,
)
from pdr_backend.lake.gql_data_factory import _GQLDF_REGISTERED_LAKE_TABLES
from pdr_backend.lake.table import ETLTable, NamedTable, TempTable
from pdr_backend.lake.prediction import Prediction
from pdr_backend.lake.table_bronze_pdr_predictions import BronzePrediction
from pdr_backend.lake.table_bronze_pdr_slots import BronzeSlot
from pdr_backend.lake.test.resources import _gql_data_factory
from pdr_backend.util.time_types import UnixTimeMs


@enforce_types
@pytest.mark.parametrize(
    "_sample_etl", [("2024-05-05", "2024-05-06")], indirect=True
)
def test_etl_tables(_sample_etl):
    _, db, gql_tables = _sample_etl

    # Assert all dfs are not the same size as mock data
    pdr_predictions_df = db.query_data("SELECT * FROM pdr_predictions")
    pdr_payouts_df = db.query_data("SELECT * FROM pdr_payouts")
    
    # Assert len of all dfs
    assert len(pdr_predictions_df) == 2057
    assert len(pdr_payouts_df) == 1870


# pylint: disable=too-many-statements
@enforce_types
@pytest.mark.parametrize(
    "_sample_etl", [("2024-05-05", "2024-05-06")], indirect=True
)
def test_etl_do_bronze_step(_sample_etl):
    etl, db, gql_tables = _sample_etl

    # assert the number of records we expect to see in final table
    table_name = NamedTable.from_dataclass(Prediction).fullname
    pdr_predictions = db.query_data(
        "SELECT * FROM {}".format(table_name)
    )
    assert len(pdr_predictions) == 2057
    assert pdr_predictions['payout'].is_null().sum() == 2057
    
    # Work 1: Do bronze
    etl.do_bronze_step()
    
    # assert bronze_pdr_predictios and related tables are created
    temp_table_name = TempTable.from_dataclass(BronzePrediction).fullname
    temp_bronze_pdr_predictions_records = db.query_data(
        "SELECT * FROM {}".format(temp_table_name)
    )
    assert temp_bronze_pdr_predictions_records['payout'].is_null().sum() == 377
    
    # move tables to production
    etl._move_from_temp_tables_to_live()
    
    # assert bronze_pdr_predictions_df is created correctly
    table_name = NamedTable.from_dataclass(BronzePrediction).fullname
    bronze_pdr_predictions_records = db.query_data(
        "SELECT * FROM {}".format(table_name)
    )
    assert bronze_pdr_predictions_records is not None
    
    assert len(bronze_pdr_predictions_records) == 2055
    assert bronze_pdr_predictions_records['payout'].is_null().sum() == 377