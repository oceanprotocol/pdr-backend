from enforce_typing import enforce_types

from pdr_backend.lake.payout import Payout
from pdr_backend.lake.persistent_data_store import PersistentDataStore
from pdr_backend.lake.prediction import Prediction
from pdr_backend.lake.table import Table, TableType, get_table_name
from pdr_backend.lake.table_bronze_pdr_predictions import (
    BronzePrediction,
    get_bronze_pdr_predictions_data_with_SQL,
)
from pdr_backend.lake.test.resources import _gql_data_factory
from pdr_backend.lake.trueval import Trueval
from pdr_backend.util.time_types import UnixTimeMs


@enforce_types
def test_table_bronze_pdr_predictions(
    _gql_datafactory_etl_payouts_df,
    _gql_datafactory_etl_predictions_df,
    _gql_datafactory_etl_truevals_df,
    tmpdir,
):
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
        "pdr_predictions": Table(Prediction, ppss),
        "pdr_truevals": Table(Trueval, ppss),
        "pdr_payouts": Table(Payout, ppss),
        "bronze_pdr_predictions": Table(BronzePrediction, ppss),
    }

    # Work 1: Append all data onto bronze_table
    gql_tables["pdr_predictions"].append_to_storage(_gql_datafactory_etl_predictions_df)
    gql_tables["pdr_truevals"].append_to_storage(_gql_datafactory_etl_truevals_df)
    gql_tables["pdr_payouts"].append_to_storage(_gql_datafactory_etl_payouts_df)

    pds = PersistentDataStore(ppss.lake_ss.lake_dir)
    # truevals should have 6
    table_name = get_table_name("pdr_truevals")
    result_truevals = pds.query_data("SELECT * FROM {}".format(table_name))
    assert len(result_truevals) == 6

    # payouts should have 6
    table_name = get_table_name("pdr_payouts")
    result_payouts = pds.query_data("SELECT * FROM {}".format(table_name))
    assert len(result_payouts) == 5

    # Work 2: Execute full SQL query
    get_bronze_pdr_predictions_data_with_SQL(
        ppss.lake_ss.lake_dir,
        st_ms=UnixTimeMs.from_timestr(ppss.lake_ss.st_timestr),
        fin_ms=UnixTimeMs.from_timestr(ppss.lake_ss.fin_timestr),
    )

    bronze_pdr_predictions_table_name = BronzePrediction.get_lake_table_name()
    result = pds.query_data(
        f"""
            SELECT * FROM {get_table_name(bronze_pdr_predictions_table_name, TableType.TEMP)}
        """
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
