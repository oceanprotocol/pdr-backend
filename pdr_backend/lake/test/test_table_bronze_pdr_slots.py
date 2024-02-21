from enforce_typing import enforce_types
from pdr_backend.lake.test.resources import _gql_data_factory
from pdr_backend.lake.table_bronze_pdr_slots import (
    _process_bronze_predictions,
    _process_slots,
    bronze_pdr_slots_schema,
    bronze_pdr_slots_table_name,
)
from pdr_backend.lake.table_bronze_pdr_predictions import (
    get_bronze_pdr_predictions_table,
)
from pdr_backend.lake.table_bronze_pdr_predictions import (
    bronze_pdr_predictions_table_name,
    bronze_pdr_predictions_schema,
)
from pdr_backend.lake.table_pdr_predictions import (
    predictions_schema,
    predictions_table_name,
)
from pdr_backend.lake.table_pdr_truevals import truevals_schema, truevals_table_name
from pdr_backend.lake.table_pdr_payouts import payouts_schema, payouts_table_name
from pdr_backend.lake.table_pdr_slots import slots_schema, slots_table_name
from pdr_backend.lake.table import Table


@enforce_types
def test_table_bronze_pdr_slots(
    _gql_datafactory_etl_slots_df,
    _gql_datafactory_etl_predictions_df,
    _gql_datafactory_etl_truevals_df,
    _gql_datafactory_etl_payouts_df,
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
        "pdr_predictions": Table(predictions_table_name, predictions_schema, ppss),
        "pdr_truevals": Table(truevals_table_name, truevals_schema, ppss),
        "pdr_payouts": Table(payouts_table_name, payouts_schema, ppss),
        "pdr_slots": Table(slots_table_name, slots_schema, ppss),
        "bronze_pdr_predictions": Table(
            bronze_pdr_predictions_table_name, bronze_pdr_predictions_schema, ppss
        ),
        "bronze_pdr_slots": Table(
            bronze_pdr_slots_table_name, bronze_pdr_slots_schema, ppss
        ),
    }

    gql_tables["pdr_predictions"].df = _gql_datafactory_etl_predictions_df
    gql_tables["pdr_truevals"].df = _gql_datafactory_etl_truevals_df
    gql_tables["pdr_payouts"].df = _gql_datafactory_etl_payouts_df
    gql_tables["pdr_slots"].df = _gql_datafactory_etl_slots_df

    gql_tables["bronze_pdr_predictions"] = get_bronze_pdr_predictions_table(
        gql_tables, ppss
    )

    assert len(gql_tables["bronze_pdr_slots"].df) == 0

    # Work 1: Append new slots onto bronze_table
    # In our mock, all predictions have None trueval, predictions, etc...
    # This shows that all of this data will come from other tables
    gql_tables = _process_slots([], gql_tables, ppss)
    assert len(gql_tables["bronze_pdr_slots"].df) == 6
    assert gql_tables["bronze_pdr_slots"].df["slot"] is not None
    assert gql_tables["bronze_pdr_slots"].df["timestamp"] is not None
    assert gql_tables["bronze_pdr_slots"].df["roundSumStakesUp"] is not None
    assert gql_tables["bronze_pdr_slots"].df["roundSumStakes"] is not None

    # Work 2: Append from bronze_pdr_predictions table
    gql_tables = _process_bronze_predictions(gql_tables, ppss)
    # We should still have 6 rows
    assert len(gql_tables["bronze_pdr_slots"].df) == 6

    # Check final data frame has all the required columns
    assert gql_tables["bronze_pdr_slots"].df.schema == bronze_pdr_slots_schema
