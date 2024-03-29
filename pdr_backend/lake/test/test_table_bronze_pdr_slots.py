from enforce_typing import enforce_types
from pdr_backend.lake.test.resources import _gql_data_factory
from pdr_backend.lake.table_bronze_pdr_slots import (
    get_bronze_pdr_slots_data_with_SQL,
    bronze_pdr_slots_schema,
    bronze_pdr_slots_table_name,
)
from pdr_backend.lake.table_bronze_pdr_predictions import (
    get_bronze_pdr_predictions_data_with_SQL,
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
from pdr_backend.lake.test.resources import _clean_up_table_registry
from pdr_backend.lake.test.conftest import _clean_up_persistent_data_store
from pdr_backend.util.time_types import UnixTimeMs
from pdr_backend.lake.plutil import get_table_name, TableType
from pdr_backend.lake.persistent_data_store import PersistentDataStore


@enforce_types
def test_table_bronze_pdr_slots(
    _gql_datafactory_etl_slots_df,
    _gql_datafactory_etl_predictions_df,
    _gql_datafactory_etl_truevals_df,
    _gql_datafactory_etl_payouts_df,
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

    _clean_up_persistent_data_store(ppss.lake_ss.lake_dir)

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

    # Work 1: Append all data onto tables
    gql_tables["pdr_predictions"].append_to_storage(
        _gql_datafactory_etl_predictions_df, TableType.TEMP
    )
    gql_tables["pdr_truevals"].append_to_storage(
        _gql_datafactory_etl_truevals_df, TableType.TEMP
    )
    gql_tables["pdr_payouts"].append_to_storage(
        _gql_datafactory_etl_payouts_df, TableType.TEMP
    )
    gql_tables["pdr_slots"].append_to_storage(
        _gql_datafactory_etl_slots_df, TableType.TEMP
    )

    # Check that the data is appended correctly
    pds = PersistentDataStore(ppss.lake_ss.lake_dir)

    pdr_slots_df = pds.query_data(
        f"""
        SELECT * FROM {get_table_name(slots_table_name, TableType.TEMP)}
        """
    )

    assert pdr_slots_df["truevalue"][0] is None
    assert pdr_slots_df["roundSumStakesUp"][0] is None
    assert pdr_slots_df["roundSumStakes"][0] is None

    bronze_pdr_predictions_df = get_bronze_pdr_predictions_data_with_SQL(
        ppss.lake_ss.lake_dir,
        st_ms=UnixTimeMs.from_timestr(ppss.lake_ss.st_timestr),
        fin_ms=UnixTimeMs.from_timestr(ppss.lake_ss.fin_timestr),
    )

    gql_tables["bronze_pdr_predictions"].append_to_storage(
        bronze_pdr_predictions_df, TableType.TEMP
    )

    bronze_pdr_slots = get_bronze_pdr_slots_data_with_SQL(
        ppss.lake_ss.lake_dir,
        st_ms=UnixTimeMs.from_timestr(ppss.lake_ss.st_timestr),
        fin_ms=UnixTimeMs.from_timestr(ppss.lake_ss.fin_timestr),
    )

    assert len(bronze_pdr_slots) == 7
    assert bronze_pdr_slots.schema == bronze_pdr_slots_schema

    assert bronze_pdr_slots["truevalue"].null_count() == 1
    assert bronze_pdr_slots["roundSumStakes"].null_count() == 2
    assert bronze_pdr_slots["source"].null_count() == 2
