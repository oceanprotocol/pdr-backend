from enforce_typing import enforce_types

from pdr_backend.lake.test.resources import _gql_data_factory
from pdr_backend.lake.table_bronze_pdr_predictions import (
    bronze_pdr_predictions_schema,
    bronze_pdr_predictions_table_name,
    get_bronze_pdr_predictions_data_with_SQL,
)
from pdr_backend.lake.table_pdr_predictions import (
    predictions_schema,
    predictions_table_name,
)
from pdr_backend.lake.table import Table
from pdr_backend.lake.table_pdr_truevals import truevals_schema, truevals_table_name
from pdr_backend.lake.table_pdr_payouts import payouts_schema, payouts_table_name
from pdr_backend.lake.persistent_data_store import PersistentDataStore
from pdr_backend.lake.test.resources import _clean_up_table_registry
from pdr_backend.util.time_types import UnixTimeMs
from pdr_backend.lake.plutil import get_table_name, TableType


@enforce_types
def test_table_bronze_pdr_predictions(
    _gql_datafactory_etl_payouts_df,
    _gql_datafactory_etl_predictions_df,
    _gql_datafactory_etl_truevals_df,
    tmpdir,
):
    _clean_up_table_registry()

    # please note date, including Nov 1st
    st_timestr = "2023-11-01_0:00"
    fin_timestr = "2023-11-07_0:00"

    ppss, _ = _gql_data_factory(
        tmpdir,
        "binanceus ETH/USDT h 5m",
        st_timestr,
        fin_timestr,
    )

    gql_tables = {
        "pdr_predictions": Table(predictions_table_name, predictions_schema, ppss),
        "pdr_truevals": Table(truevals_table_name, truevals_schema, ppss),
        "pdr_payouts": Table(payouts_table_name, payouts_schema, ppss),
        "bronze_pdr_predictions": Table(
            bronze_pdr_predictions_table_name, bronze_pdr_predictions_schema, ppss
        ),
    }

    # Work 1: Append all data onto bronze_table
    gql_tables["pdr_predictions"].append_to_storage(
        _gql_datafactory_etl_predictions_df, TableType.TEMP
    )
    gql_tables["pdr_truevals"].append_to_storage(_gql_datafactory_etl_truevals_df, TableType.TEMP)
    gql_tables["pdr_payouts"].append_to_storage(_gql_datafactory_etl_payouts_df, TableType.TEMP)

    pds = PersistentDataStore(ppss.lake_ss.parquet_dir)
    # truevals should have 6
    temp_table_name = get_table_name("pdr_truevals", TableType.TEMP)
    result_truevals = pds.query_data("SELECT * FROM {}".format(temp_table_name))
    assert len(result_truevals) == 6

    # payouts should have 6
    temp_table_name = get_table_name("pdr_payouts", TableType.TEMP)
    result_payouts = pds.query_data("SELECT * FROM {}".format(temp_table_name))
    assert len(result_payouts) == 5

    # Work 2: Execute full SQL query
    result = get_bronze_pdr_predictions_data_with_SQL(
        ppss.lake_ss.parquet_dir,
        st_ms=UnixTimeMs.from_timestr(ppss.lake_ss.st_timestr),
        fin_ms=UnixTimeMs.from_timestr(ppss.lake_ss.fin_timestr),
    )

    # Final result should have 6 rows
    assert len(result) == 6

    # Assert that there will be 1 null value in every column we're joining
    assert result["truevalue"].null_count() == 1
    assert result["stake"].null_count() == 1
    assert result["payout"].null_count() == 1

    # Validate stake is what we expect
    target_stake = [5.46, 5.46, 3.46, 3.46, 3.46, None]
    bronze_pdr_predictions_stake = result["stake"].to_list()
    for actual_stake, expected_stake in zip(bronze_pdr_predictions_stake, target_stake):
        if actual_stake is None:
            assert actual_stake == expected_stake
        else:
            assert round(actual_stake, 2) == expected_stake

    # Validate payout is what we expect
    target_payout = [0.00, 10.93, 7.04, 7.16, 0.0, None]
    bronze_pdr_predictions_payout = result["payout"].to_list()
    for actual_payout, expected_payout in zip(
        bronze_pdr_predictions_payout, target_payout
    ):
        if actual_payout is None:
            assert actual_payout == expected_payout
        else:
            assert round(actual_payout, 2) == expected_payout
