#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from enforce_typing import enforce_types

import polars as pl

from pdr_backend.lake.table import Table, NewEventsTable
from pdr_backend.lake.prediction import Prediction
from pdr_backend.lake.payout import Payout
from pdr_backend.lake.table_bronze_pdr_predictions import BronzePrediction


@enforce_types
@pytest.mark.parametrize(
    "_sample_etl", [("2024-07-26_00:00", "2024-07-26_02:00", False)], indirect=True
)
def test_etl_tables(_sample_etl):
    _, db, _ = _sample_etl

    # Assert all dfs are not the same size as mock data
    pdr_predictions_df = db.query_data("SELECT * FROM pdr_predictions")
    pdr_payouts_df = db.query_data("SELECT * FROM pdr_payouts")
    pdr_truevals_df = db.query_data("SELECT * FROM pdr_truevals")
    pdr_subscriptions_df = db.query_data("SELECT * FROM pdr_subscriptions")
    pdr_slots_df = db.query_data("SELECT * FROM pdr_slots")

    # Assert len of all dfs
    assert len(pdr_predictions_df) == 2369
    assert len(pdr_payouts_df) == 2349
    assert len(pdr_truevals_df) == 260
    assert len(pdr_subscriptions_df) == 2140
    assert len(pdr_slots_df) == 260


# pylint: disable=too-many-statements
@enforce_types
@pytest.mark.parametrize(
    "_sample_etl", [("2024-07-26_00:00", "2024-07-26_02:00", True)], indirect=True
)
def test_etl_do_bronze_step(_sample_etl):
    etl, db, _ = _sample_etl

    # assert the number of predictions we expect to see in prod table
    # assert all predictions have null payouts
    table_name = Table.from_dataclass(Prediction).table_name
    pdr_predictions = db.query_data("SELECT * FROM {}".format(table_name))
    expected_pdr_predictions = len(pdr_predictions)
    assert expected_pdr_predictions == 2369

    # all predictions have null payouts
    assert pdr_predictions["payout"].is_null().sum() == 2369

    # assert we have valid payouts to join with predictions
    table_name = Table.from_dataclass(Payout).table_name
    pdr_payouts = db.query_data("SELECT * FROM {}".format(table_name))
    expected_pdr_payouts = len(pdr_payouts)
    assert expected_pdr_payouts == 2349

    # all payouts have have payout values
    assert pdr_payouts["payout"].is_null().sum() == 0

    # Work 1: Do bronze
    etl.do_bronze_step()

    # assert bronze_pdr_predictios and related tables are created correctly
    new_events_bronze_pdr_predictions_table = NewEventsTable.from_dataclass(
        BronzePrediction
    )
    records = db.query_data(
        "SELECT * FROM {}".format(new_events_bronze_pdr_predictions_table.table_name)
    )

    prod_bronze_pdr_predictions_null_payouts = records["payout"].is_null().sum()
    prod_bronze_pdr_predictions_valid_payouts = records["payout"].is_not_null().sum()

    # assert temp_bronze_pdr_predictions table that will be moved to production
    assert prod_bronze_pdr_predictions_null_payouts == 349
    assert prod_bronze_pdr_predictions_valid_payouts == 2020
    assert (
        prod_bronze_pdr_predictions_null_payouts
        + prod_bronze_pdr_predictions_valid_payouts
        == expected_pdr_predictions
    )

    # move tables to production
    etl._do_bronze_swap_to_prod_atomic()

    # assert bronze_pdr_predictions_df is created correctly
    table_name = Table.from_dataclass(BronzePrediction).table_name
    bronze_pdr_predictions_records = db.query_data(
        "SELECT * FROM {}".format(table_name)
    )
    assert bronze_pdr_predictions_records is not None

    # verify final production table
    prod_bronze_pdr_predictions_null_payouts = (
        bronze_pdr_predictions_records["payout"].is_null().sum()
    )
    prod_bronze_pdr_predictions_valid_payouts = (
        bronze_pdr_predictions_records["payout"].is_not_null().sum()
    )

    # all predictions with valid payouts that can be joined, have been updated
    assert prod_bronze_pdr_predictions_null_payouts == 349
    assert prod_bronze_pdr_predictions_valid_payouts == 2020
    assert (
        prod_bronze_pdr_predictions_null_payouts
        + prod_bronze_pdr_predictions_valid_payouts
        == expected_pdr_predictions
    )


# pylint: disable=too-many-statements
@enforce_types
@pytest.mark.parametrize(
    "_sample_etl", [("2024-07-26_00:00", "2024-07-26_00:40", True)], indirect=True
)
def test_etl_do_incremental_bronze_step(_sample_raw_data, _sample_etl):
    etl, db, gql_tables = _sample_etl

    # We are gonna operate the ETL manually in 3 steps
    etl._clamp_checkpoints_to_ppss = True

    def _step1():
        # Step 1: 00:00 - 00:40
        # get all predictions we expect to end up in bronze table
        prediction_table = Table.from_dataclass(Prediction).table_name
        query = f"""
        SELECT 
            * 
        FROM {prediction_table}
        where
            {prediction_table}.timestamp >= {etl.ppss.lake_ss.st_timestamp}
            and {prediction_table}.timestamp <= {etl.ppss.lake_ss.fin_timestamp}
        """
        expected_rows = db.query_data(query)
        assert len(expected_rows) == 741

        # execute the ETL
        etl.do_bronze_step()
        etl._do_bronze_swap_to_prod_atomic()

        # get all bronze_pdr_predictions for this period
        bronze_prediction_table = Table.from_dataclass(BronzePrediction).table_name
        query = f"""
        SELECT 
            * 
        FROM {bronze_prediction_table}
        where
            {bronze_prediction_table}.timestamp >= {etl.ppss.lake_ss.st_timestamp}
            and {bronze_prediction_table}.timestamp <= {etl.ppss.lake_ss.fin_timestamp}
        """
        bronze_pdr_predictions_records = db.query_data(query)

        # get count of null and valid prediction.payouts
        prod_null_payouts = bronze_pdr_predictions_records["payout"].is_null().sum()
        prod_valid_payouts = (
            bronze_pdr_predictions_records["payout"].is_not_null().sum()
        )

        # assert those numbers so we can track progress
        assert prod_null_payouts == 209
        assert prod_valid_payouts == 532

        # validate that rows are equal to what we expected
        assert prod_null_payouts + prod_valid_payouts == len(expected_rows)

    def _step2():
        # Step 2: 00:40 - 01:20
        # override ppss timestamps
        etl.ppss.lake_ss.d["st_timestr"] = "2024-07-26_00:40:01"
        etl.ppss.lake_ss.d["fin_timestr"] = "2024-07-26_01:20:00"

        # sim gql_data_factory saving data to storage so it can be processed
        _sample_predictions = (
            _sample_raw_data["pdr_predictions"]
            .filter(pl.col("timestamp") >= etl.ppss.lake_ss.st_timestamp)
            .filter(pl.col("timestamp") <= etl.ppss.lake_ss.fin_timestamp)
        )

        _sample_payouts = (
            _sample_raw_data["pdr_payouts"]
            .filter(pl.col("timestamp") >= etl.ppss.lake_ss.st_timestamp)
            .filter(pl.col("timestamp") <= etl.ppss.lake_ss.fin_timestamp)
        )

        def _transform_columns(df, dtype_mapping):
            for column, dtype in dtype_mapping.items():
                df = df.with_columns(df[column].cast(dtype).alias(column))
            return df

        _sample_predictions = _transform_columns(
            _sample_predictions, Prediction.get_lake_schema()
        )
        _sample_payouts = _transform_columns(_sample_payouts, Payout.get_lake_schema())

        gql_tables["pdr_predictions"].append_to_storage(_sample_predictions, etl.ppss)
        gql_tables["pdr_payouts"].append_to_storage(_sample_payouts, etl.ppss)

        # get all predictions we expect to end up in bronze table
        prediction_table = Table.from_dataclass(Prediction).table_name
        query = f"""
        SELECT 
            * 
        FROM {prediction_table}
        where
            {prediction_table}.timestamp >= {etl.ppss.lake_ss.st_timestamp}
            and {prediction_table}.timestamp <= {etl.ppss.lake_ss.fin_timestamp}
        """
        expected_rows = db.query_data(query)
        assert len(expected_rows) == 824

        # execute the ETL
        etl.do_bronze_step()
        etl._do_bronze_swap_to_prod_atomic()

        # get all bronze_pdr_predictions for this period
        bronze_prediction_table = Table.from_dataclass(BronzePrediction).table_name
        query = f"""
        SELECT 
            * 
        FROM {bronze_prediction_table}
        where
            {bronze_prediction_table}.timestamp >= {etl.ppss.lake_ss.st_timestamp}
            and {bronze_prediction_table}.timestamp <= {etl.ppss.lake_ss.fin_timestamp}
        """
        bronze_pdr_predictions_records = db.query_data(query)

        # get count of null and valid prediction.payouts
        prod_null_payouts = bronze_pdr_predictions_records["payout"].is_null().sum()
        prod_valid_payouts = (
            bronze_pdr_predictions_records["payout"].is_not_null().sum()
        )

        # assert those numbers so we can track progress
        assert prod_null_payouts == 269
        assert prod_valid_payouts == 555

        # validate that rows are equal to what we expected
        assert prod_null_payouts + prod_valid_payouts == len(expected_rows)

    def _step3():
        # Step 3: 01:20 - 02:00
        # override ppss timestamps
        etl.ppss.lake_ss.d["st_timestr"] = "2024-07-26_01:20:01"
        etl.ppss.lake_ss.d["fin_timestr"] = "2024-07-26_02:00:00"

        # sim gql_data_factory saving data to storage so it can be processed
        _sample_predictions = (
            _sample_raw_data["pdr_predictions"]
            .filter(pl.col("timestamp") >= etl.ppss.lake_ss.st_timestamp)
            .filter(pl.col("timestamp") <= etl.ppss.lake_ss.fin_timestamp)
        )

        _sample_payouts = (
            _sample_raw_data["pdr_payouts"]
            .filter(pl.col("timestamp") >= etl.ppss.lake_ss.st_timestamp)
            .filter(pl.col("timestamp") <= etl.ppss.lake_ss.fin_timestamp)
        )

        def _transform_columns(df, dtype_mapping):
            for column, dtype in dtype_mapping.items():
                df = df.with_columns(df[column].cast(dtype).alias(column))
            return df

        _sample_predictions = _transform_columns(
            _sample_predictions, Prediction.get_lake_schema()
        )
        _sample_payouts = _transform_columns(_sample_payouts, Payout.get_lake_schema())

        gql_tables["pdr_predictions"].append_to_storage(_sample_predictions, etl.ppss)
        gql_tables["pdr_payouts"].append_to_storage(_sample_payouts, etl.ppss)

        # get all predictions we expect to end up in bronze table
        prediction_table = Table.from_dataclass(Prediction).table_name
        query = f"""
        SELECT 
            * 
        FROM {prediction_table}
        where
            {prediction_table}.timestamp >= {etl.ppss.lake_ss.st_timestamp}
            and {prediction_table}.timestamp <= {etl.ppss.lake_ss.fin_timestamp}
        """
        expected_rows = db.query_data(query)
        assert len(expected_rows) == 804

        # execute the ETL
        etl.do_bronze_step()
        etl._do_bronze_swap_to_prod_atomic()

        # get all bronze_pdr_predictions for this period
        bronze_prediction_table = Table.from_dataclass(BronzePrediction).table_name
        query = f"""
        SELECT 
            * 
        FROM {bronze_prediction_table}
        where
            {bronze_prediction_table}.timestamp >= {etl.ppss.lake_ss.st_timestamp}
            and {bronze_prediction_table}.timestamp <= {etl.ppss.lake_ss.fin_timestamp}
        """
        bronze_pdr_predictions_records = db.query_data(query)

        # get count of null and valid prediction.payouts
        prod_null_payouts = bronze_pdr_predictions_records["payout"].is_null().sum()
        prod_valid_payouts = (
            bronze_pdr_predictions_records["payout"].is_not_null().sum()
        )

        # assert those numbers so we can track progress
        assert prod_null_payouts == 249
        assert prod_valid_payouts == 555

        # validate that rows are equal to what we expected
        assert prod_null_payouts + prod_valid_payouts == len(expected_rows)

    _step1()
    _step2()
    _step3()

    # assert bronze_pdr_predictions_df is created correctly
    bronze_table_name = Table.from_dataclass(BronzePrediction).table_name
    query = f"""SELECT * FROM {bronze_table_name}"""
    bronze_pdr_predictions_records = db.query_data(query)
    # bronze_pdr_predictions_records.write_csv('final_bronze_pdr_predictions_records.csv')

    # verify final production table
    prod_null_payouts = bronze_pdr_predictions_records["payout"].is_null().sum()
    prod_valid_payouts = bronze_pdr_predictions_records["payout"].is_not_null().sum()

    #
    assert prod_null_payouts == 349
    assert prod_valid_payouts == 2020
    assert bronze_pdr_predictions_records.shape[0] == 2369
    assert (
        prod_null_payouts + prod_valid_payouts
        == bronze_pdr_predictions_records.shape[0]
    )


# pylint: disable=too-many-statements
@enforce_types
@pytest.mark.parametrize(
    "_sample_etl", [("2024-07-26_00:00", "2024-07-26_00:40", True)], indirect=True
)
def test_etl_do_incremental_broken_date_bronze_step(_sample_etl):
    etl, db, _ = _sample_etl

    # We are gonna operate the ETL manually in 3 steps
    etl._clamp_checkpoints_to_ppss = True
    prediction_table = Table.from_dataclass(Prediction).table_name
    bronze_prediction_table = Table.from_dataclass(BronzePrediction).table_name

    def _step1():
        # Step 1: 00:00 - 00:40
        # get all predictions we expect to end up in bronze table
        query = f"""
        SELECT 
            * 
        FROM {prediction_table}
        where
            {prediction_table}.timestamp >= {etl.ppss.lake_ss.st_timestamp}
            and {prediction_table}.timestamp <= {etl.ppss.lake_ss.fin_timestamp}
        """
        expected_rows = db.query_data(query)
        assert len(expected_rows) == 741

        # execute the ETL
        etl.do_bronze_step()
        etl._do_bronze_swap_to_prod_atomic()

        # get all bronze_pdr_predictions for this period
        bronze_prediction_table = Table.from_dataclass(BronzePrediction).table_name
        query = f"""
        SELECT 
            * 
        FROM {bronze_prediction_table}
        where
            {bronze_prediction_table}.timestamp >= {etl.ppss.lake_ss.st_timestamp}
            and {bronze_prediction_table}.timestamp <= {etl.ppss.lake_ss.fin_timestamp}
        """
        bronze_pdr_predictions_records = db.query_data(query)

        # get count of null and valid prediction.payouts
        prod_null_payouts = bronze_pdr_predictions_records["payout"].is_null().sum()
        prod_valid_payouts = (
            bronze_pdr_predictions_records["payout"].is_not_null().sum()
        )

        # assert those numbers so we can track progress
        assert prod_null_payouts == 209
        assert prod_valid_payouts == 532

        # validate that rows are equal to what we expected
        assert prod_null_payouts + prod_valid_payouts == len(expected_rows)

    def _step2_introduce_error_in_date():
        # Step 2: 00:00 - 00:35
        # new_payouts -> 0
        # new_predictions -> 0
        # new bronze_pdr_predictions -> 0

        # disable clamp so checkpoint algo runs
        etl._clamp_checkpoints_to_ppss = False

        # override ppss timestamps to a date we aleady processed
        # this introduces room for errors and duplicates
        etl.ppss.lake_ss.d["st_timestr"] = "2024-07-26_00:00"
        etl.ppss.lake_ss.d["fin_timestr"] = "2024-07-26_00:35"

        # execute the ETL
        etl.do_bronze_step()

        # do the final swap
        etl._do_bronze_swap_to_prod_atomic()

        # get all bronze_pdr_predictions for this period
        bronze_prediction_table = Table.from_dataclass(BronzePrediction).table_name

        # validate we have 0 duplicates
        query_duplicate_summary = f"""
            SELECT
                '{bronze_prediction_table}' as table_name,
                COUNT(*) as incident_count
            FROM (
                SELECT
                    ID as ID,
                    timestamp,
                FROM {bronze_prediction_table}
                GROUP BY ID, timestamp
                HAVING COUNT(*) > 1
            ) as inner_query
            GROUP BY table_name
        """
        duplicate_records = db.query_data(query_duplicate_summary)
        assert len(duplicate_records) == 0

    _step1()
    _step2_introduce_error_in_date()

    # get count of final prod table
    bronze_pdr_predictions_records = db.query_data(
        f"SELECT * FROM {bronze_prediction_table}"
    )
    prod_null_payouts = bronze_pdr_predictions_records["payout"].is_null().sum()
    prod_valid_payouts = bronze_pdr_predictions_records["payout"].is_not_null().sum()

    assert prod_null_payouts == 209
    assert prod_valid_payouts == 532
