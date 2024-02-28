from enforce_typing import enforce_types
from pdr_backend.lake.test.resources import _gql_data_factory
from pdr_backend.lake.table_bronze_pdr_slots import (
    _process_payouts,
    _process_bronze_predictions,
    _process_slots,
    _process_truevals,
    get_bronze_pdr_slots_table,
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
import polars as pl


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

    assert gql_tables["pdr_slots"].df["trueval"][0] is None
    assert gql_tables["pdr_slots"].df["roundSumStakesUp"][0] is None
    assert gql_tables["pdr_slots"].df["roundSumStakes"][0] is None

    gql_tables["bronze_pdr_predictions"] = get_bronze_pdr_predictions_table(
        gql_tables, ppss
    )

    assert len(gql_tables["bronze_pdr_slots"].df) == 0

    # Work 1: Append new slots onto bronze_table
    # In our mock, all predictions have None trueval, predictions, etc...
    # This shows that all of this data will come from other tables
    gql_tables = _process_slots([], gql_tables, ppss)

    assert len(gql_tables["bronze_pdr_slots"].df) == 7
    assert gql_tables["bronze_pdr_slots"].df["slot"][0] is not None
    assert gql_tables["bronze_pdr_slots"].df["timestamp"][0] is not None

    assert gql_tables["bronze_pdr_slots"].df["trueval"].null_count() == len(
        gql_tables["bronze_pdr_slots"].df
    )
    assert gql_tables["bronze_pdr_slots"].df["roundSumStakesUp"].null_count() == len(
        gql_tables["bronze_pdr_slots"].df
    )
    assert gql_tables["bronze_pdr_slots"].df["roundSumStakes"].null_count() == len(
        gql_tables["bronze_pdr_slots"].df
    )

    # Work 2: Append from pdr_truevals table
    gql_tables = _process_truevals(gql_tables, ppss)
    assert None in gql_tables["bronze_pdr_slots"].df["trueval"].to_list()

    # We should have 2 slots with no trueval submitted
    assert (
        sum(
            1
            for item in gql_tables["bronze_pdr_slots"].df["trueval"].to_list()
            if item is None
        )
        == 1
    )

    # Work 3: Append from bronze_pdr_predictions table
    gql_tables = _process_bronze_predictions(gql_tables, ppss)
    # We should still have 7 rows, last prediction is filtered out
    assert len(gql_tables["bronze_pdr_slots"].df) == 7

    # Check final data frame has all the required columns
    assert gql_tables["bronze_pdr_slots"].df.schema == bronze_pdr_slots_schema

    # Work 4: Append from pdr_payouts table
    gql_tables = _process_payouts(gql_tables, ppss)

    # Let's simulate new event and test that tables are getting updated

    # Add 2 new Prediction events for 1699315100 slot
    new_row = pl.DataFrame(
        {
            "ID": "0x30f1c55e72fe105e4a1fbecdff3145fc14177695-1699315100-0lx2a24cb4ff2584bad80ff5f109034a891c3d72ee",
            "contract": "0x30f1c55e72fe105e4a1fbecdff3145fc14177695",
            "pair": "ETH/USDT",
            "timeframe": "5m",
            "prediction": None,
            "stake": None,
            "trueval": None,
            "timestamp": 1698865200,
            "source": "binance",
            "payout": None,
            "slot": 1699315100,
            "user": "0lx2a24cb4ff2584bad80ff5f109034a891c3d72ee",
        }
    )
    new_row_2 = pl.DataFrame(
        {
            "ID": "0x30f1c55e72fe105e4a1fbecdff3145fc14177695-1699315100-0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
            "contract": "0x30f1c55e72fe105e4a1fbecdff3145fc14177695",
            "pair": "ETH/USDT",
            "timeframe": "5m",
            "prediction": None,
            "stake": None,
            "trueval": None,
            "timestamp": 1698951300,
            "source": "binance",
            "payout": None,
            "slot": 1699315100,
            "user": "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
        }
    )
    gql_tables["pdr_predictions"].df = gql_tables["pdr_predictions"].df.vstack(new_row)
    gql_tables["pdr_predictions"].df = gql_tables["pdr_predictions"].df.vstack(
        new_row_2
    )
    gql_tables["bronze_pdr_predictions"] = get_bronze_pdr_predictions_table(
        gql_tables, ppss
    )

    gql_tables["bronze_pdr_slots"] = get_bronze_pdr_slots_table(gql_tables, ppss)

    # We should have 1 slot with no trueval submitted
    assert (
        sum(
            1
            for item in gql_tables["bronze_pdr_slots"].df["trueval"].to_list()
            if item is None
        )
        == 1
    )

    # Add new trueval event
    new_row = pl.DataFrame(
        {
            "ID": "0x30f1c55e72fe105e4a1fbecdff3145fc14177695-1699315100",
            "token": "ETH/USDT",
            "timestamp": 1699315101000,
            "trueval": False,
            "slot": 1699315100000,
        }
    )
    gql_tables["pdr_truevals"].df = gql_tables["pdr_truevals"].df.vstack(new_row)
    gql_tables["bronze_pdr_predictions"] = get_bronze_pdr_predictions_table(
        gql_tables, ppss
    )

    gql_tables["bronze_pdr_slots"] = get_bronze_pdr_slots_table(gql_tables, ppss)

    # We should have 1 slot with no trueval submitted
    assert (
        sum(
            1
            for item in gql_tables["bronze_pdr_slots"].df["trueval"].to_list()
            if item is None
        )
        == 0
    )

    # Add new payout events
    new_row = pl.DataFrame(
        {
            "ID": "0x30f1c55e72fe105e4a1fbecdff3145fc14177695-1699315100",
            "token": "ETH/USDT",
            "user": "0lx2a24cb4ff2584bad80ff5f109034a891c3d72ee",
            "slot": 1699315100000,
            "timestamp": 1699315102000,
            "payout": 200.0,
            "predictedValue": False,
            "revenue": 200.0,
            "roundSumStakesUp": 100.0,
            "roundSumStakes": 100.0,
            "stake": 100.0,
        }
    )
    new_row2 = pl.DataFrame(
        {
            "ID": "0x30f1c55e72fe105e4a1fbecdff3145fc14177695-1699315100",
            "token": "ETH/USDT",
            "user": "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
            "slot": 1699315100000,
            "timestamp": 1699315104000,
            "payout": 0.0,
            "predictedValue": True,
            "revenue": 0.0,
            "roundSumStakesUp": 0.0,
            "roundSumStakes": 200.0,
            "stake": 200.0,
        }
    )
    gql_tables["pdr_payouts"].df = gql_tables["pdr_payouts"].df.vstack(new_row)
    gql_tables["pdr_payouts"].df = gql_tables["pdr_payouts"].df.vstack(new_row2)
    gql_tables["bronze_pdr_predictions"] = get_bronze_pdr_predictions_table(
        gql_tables, ppss
    )

    gql_tables["bronze_pdr_slots"] = get_bronze_pdr_slots_table(gql_tables, ppss)

    # We should have the roundSumStakes value updated withe the stakes from latest payout event
    assert gql_tables["bronze_pdr_slots"].df["roundSumStakes"][6] == 200
    assert gql_tables["bronze_pdr_slots"].df["roundSumStakesUp"][6] == 2
