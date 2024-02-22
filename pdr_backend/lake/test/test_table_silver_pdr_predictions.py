from enforce_typing import enforce_types

from pdr_backend.lake.test.resources import _gql_data_factory
from pdr_backend.lake.table_bronze_pdr_predictions import (
    get_bronze_pdr_predictions_table,
    bronze_pdr_predictions_schema,
    bronze_pdr_predictions_table_name,
)
from pdr_backend.lake.table_silver_pdr_predictions import (
    get_silver_pdr_predictions_table,
    silver_pdr_predictions_table_name,
    silver_pdr_predictions_schema,
)
from pdr_backend.lake.table_pdr_predictions import (
    predictions_schema,
    predictions_table_name,
)
from pdr_backend.lake.table import Table
from pdr_backend.lake.table_pdr_truevals import truevals_schema, truevals_table_name
from pdr_backend.lake.table_pdr_payouts import payouts_schema, payouts_table_name


@enforce_types
def test_silver_bronze_pdr_predictions(
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
        "pdr_predictions": Table(predictions_table_name, predictions_schema, ppss),
        "pdr_truevals": Table(truevals_table_name, truevals_schema, ppss),
        "pdr_payouts": Table(payouts_table_name, payouts_schema, ppss),
        "bronze_pdr_predictions": Table(
            bronze_pdr_predictions_table_name, bronze_pdr_predictions_schema, ppss
        ),
        "silver_pdr_predictions": Table(
            silver_pdr_predictions_table_name, silver_pdr_predictions_schema, ppss
        ),
    }

    gql_tables["pdr_predictions"].df = _gql_datafactory_etl_predictions_df
    gql_tables["pdr_truevals"].df = _gql_datafactory_etl_truevals_df
    gql_tables["pdr_payouts"].df = _gql_datafactory_etl_payouts_df
    gql_tables["pdr_payouts"].df = get_bronze_pdr_predictions_table(gql_tables, ppss)

    assert len(gql_tables[bronze_pdr_predictions_table_name].df) == 6

    # Check that the silver predictions table has the right schema and length
    get_silver_pdr_predictions_table(gql_tables, ppss)
    assert len(gql_tables[silver_pdr_predictions_table_name].df) == 6
    assert (
        gql_tables[silver_pdr_predictions_table_name].df_schema
        == silver_pdr_predictions_schema
    )
