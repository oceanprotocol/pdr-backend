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
from pdr_backend.lake.payout import Payout
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

    # assert the number of predictions we expect to see in prod table
    # assert all predictions have null payouts
    table_name = NamedTable.from_dataclass(Prediction).fullname
    pdr_predictions = db.query_data(
        "SELECT * FROM {}".format(table_name)
    )
    assert len(pdr_predictions) == 2057
    assert pdr_predictions['payout'].is_null().sum() == 2057

    # assert we have valid payouts to join with predictions
    table_name = NamedTable.from_dataclass(Payout).fullname
    pdr_payouts = db.query_data(
        "SELECT * FROM {}".format(table_name)
    )
    assert len(pdr_payouts) == 1870
    assert pdr_payouts['payout'].is_null().sum() == 0
    
    # Work 1: Do bronze
    etl.do_bronze_step()
    
    # assert bronze_pdr_predictios and related tables are created correctly
    temp_table_name = TempTable.from_dataclass(BronzePrediction).fullname
    temp_bronze_pdr_predictions_records = db.query_data(
        "SELECT * FROM {}".format(temp_table_name)
    )
    null_payouts = temp_bronze_pdr_predictions_records['payout'].is_null().sum()
    valid_payouts = temp_bronze_pdr_predictions_records['payout'].is_not_null().sum()
    
    # assert temp_bronze_pdr_predictions table that will be moved to production
    assert null_payouts == 377
    assert valid_payouts == 1678
    assert null_payouts + valid_payouts == 2055
    
    # move tables to production
    etl._move_from_temp_tables_to_live()
    
    # assert bronze_pdr_predictions_df is created correctly
    table_name = NamedTable.from_dataclass(BronzePrediction).fullname
    bronze_pdr_predictions_records = db.query_data(
        "SELECT * FROM {}".format(table_name)
    )
    assert bronze_pdr_predictions_records is not None
    
    # verify final production table
    prod_null_payouts = bronze_pdr_predictions_records['payout'].is_null().sum()
    prod_valid_payouts = bronze_pdr_predictions_records['payout'].is_not_null().sum()

    assert prod_null_payouts == 377
    assert prod_valid_payouts == 1678
    assert prod_null_payouts + prod_valid_payouts == 2055


# pylint: disable=too-many-statements
@enforce_types
@pytest.mark.parametrize(
    "_sample_etl", [("2024-05-05_00:00", "2024-05-05_00:30")], indirect=True
)
def test_etl_do_incremental_bronze_step(_sample_etl):
    etl, db, gql_tables = _sample_etl
    etl._clamp_checkpoints_to_ppss = True
    
    # Step 1: 00:00 - 00:30
    # get all predictions we expect to end up in bronze table
    prediction_table = NamedTable.from_dataclass(Prediction).fullname
    query = f"""
    SELECT 
        * 
    FROM {prediction_table}
    where
        {prediction_table}.timestamp >= {etl.ppss.lake_ss.st_timestamp}
        and {prediction_table}.timestamp < {etl.ppss.lake_ss.fin_timestamp}
    """
    expcted_rows = db.query_data(query)
    assert len(expcted_rows) == 325

    # execute the ETL
    etl.do_bronze_step()
    etl._move_from_temp_tables_to_live()
    
    # get all bronze_pdr_predictions
    table_name = NamedTable.from_dataclass(BronzePrediction).fullname
    bronze_pdr_predictions_records = db.query_data(
        "SELECT * FROM {}".format(table_name)
    )
    
    # get count of null and valid prediction.payouts
    prod_null_payouts = bronze_pdr_predictions_records['payout'].is_null().sum()
    prod_valid_payouts = bronze_pdr_predictions_records['payout'].is_not_null().sum()

    # assert those numbers so we can track progress
    assert prod_null_payouts == 158
    assert prod_valid_payouts == 167

    # validate that rows are equal to what we expected
    assert prod_null_payouts + prod_valid_payouts == len(expcted_rows)