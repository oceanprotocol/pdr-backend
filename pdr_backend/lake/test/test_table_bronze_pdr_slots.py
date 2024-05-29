from enforce_typing import enforce_types

from pdr_backend.lake.payout import Payout
from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.lake.prediction import Prediction
from pdr_backend.lake.slot import Slot
from pdr_backend.lake.table import ETLTable, NamedTable, TempTable
from pdr_backend.lake.table_bronze_pdr_predictions import (
    BronzePrediction,
    get_bronze_pdr_predictions_data_with_SQL,
)
from pdr_backend.lake.table_bronze_pdr_slots import (
    BronzeSlot,
    get_bronze_pdr_slots_data_with_SQL,
)
from pdr_backend.lake.test.resources import _gql_data_factory
from pdr_backend.lake.trueval import Trueval
from pdr_backend.util.time_types import UnixTimeMs


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
        "pdr_predictions": NamedTable.from_dataclass(Prediction),
        "pdr_truevals": NamedTable.from_dataclass(Trueval),
        "pdr_payouts": NamedTable.from_dataclass(Payout),
        "pdr_slots": NamedTable.from_dataclass(Slot),
        "bronze_pdr_predictions": NamedTable.from_dataclass(BronzePrediction),
        "bronze_pdr_slots": NamedTable.from_dataclass(BronzeSlot),
    }

    # Work 1: Append all data onto tables
    gql_tables["pdr_predictions"].append_to_storage(
        _gql_datafactory_etl_predictions_df, ppss
    )
    gql_tables["pdr_truevals"].append_to_storage(_gql_datafactory_etl_truevals_df, ppss)
    gql_tables["pdr_payouts"].append_to_storage(_gql_datafactory_etl_payouts_df, ppss)
    gql_tables["pdr_slots"].append_to_storage(_gql_datafactory_etl_slots_df, ppss)

    # Check that the data is appended correctly
    db = DuckDBDataStore(ppss.lake_ss.lake_dir)

    slots_table_prefixed_name = NamedTable.from_dataclass(Slot).fullname
    pdr_slots_df = db.query_data(
        f"""
        SELECT * FROM {slots_table_prefixed_name}
        """
    )

    assert pdr_slots_df["truevalue"][0] is None
    assert pdr_slots_df["roundSumStakesUp"][0] is None
    assert pdr_slots_df["roundSumStakes"][0] is None

    get_bronze_pdr_predictions_data_with_SQL(
        ppss.lake_ss.lake_dir,
        st_ms=UnixTimeMs.from_timestr(ppss.lake_ss.st_timestr),
        fin_ms=UnixTimeMs.from_timestr(ppss.lake_ss.fin_timestr),
    )

    # Create etl view for bronze_pdr_slots
    view_query = """
            CREATE VIEW {}
            AS SELECT * FROM {}
        """.format(
        ETLTable.from_dataclass(BronzePrediction).fullname,
        TempTable.from_dataclass(BronzePrediction).fullname,
    )

    db.execute_sql(view_query)

    get_bronze_pdr_slots_data_with_SQL(
        ppss.lake_ss.lake_dir,
        st_ms=UnixTimeMs.from_timestr(ppss.lake_ss.st_timestr),
        fin_ms=UnixTimeMs.from_timestr(ppss.lake_ss.fin_timestr),
    )

    bronze_pdr_slots_temp_table_name = TempTable.from_dataclass(BronzeSlot).fullname

    bronze_pdr_slots = db.query_data(
        f"""
        SELECT * FROM {bronze_pdr_slots_temp_table_name}
        """
    )

    pdr_slots = db.query_data("""SELECT * FROM pdr_slots""")

    assert len(bronze_pdr_slots) == 7
    assert bronze_pdr_slots.schema == BronzeSlot.get_lake_schema()

    assert bronze_pdr_slots["truevalue"].null_count() == 1
    assert bronze_pdr_slots["roundSumStakes"].null_count() == 2
    assert bronze_pdr_slots["source"].null_count() == 0

    # bronze_pdr_slots should have the same amount of rows as pdr_slots
    # last item from the pdr_slots is filtered out by fin_ms
    assert len(bronze_pdr_slots) == len(pdr_slots) - 1

    ## test data without filtering

    # delete current rows from the bronze table
    db.query_data(
        f"""
        DELETE FROM {bronze_pdr_slots_temp_table_name}
        """
    )

    # query the data again with a new end date that doesn't filter out anything from pdr_slots
    get_bronze_pdr_slots_data_with_SQL(
        ppss.lake_ss.lake_dir,
        st_ms=UnixTimeMs.from_timestr(ppss.lake_ss.st_timestr),
        fin_ms=UnixTimeMs.from_timestr("2023-11-10_0:00"),
    )

    # select new data from bronze table
    bronze_pdr_slots = db.query_data(
        f"""
        SELECT * FROM {bronze_pdr_slots_temp_table_name}
        """
    )

    # check that if not filtered, the two tables should have the same length
    assert len(bronze_pdr_slots) == len(pdr_slots)
