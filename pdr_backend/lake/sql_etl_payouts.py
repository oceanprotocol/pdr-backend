from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.util.time_types import UnixTimeMs
from pdr_backend.lake.table import NamedTable, UpdateTable
from pdr_backend.lake.payout import Payout
from pdr_backend.lake.table_bronze_pdr_predictions import BronzePrediction

def _do_sql_payouts(
        db: DuckDBDataStore, 
        st_ms: UnixTimeMs,
        fin_ms: UnixTimeMs ) -> None:
    
    payout_table = NamedTable.from_dataclass(Payout)
    update_bronze_prediction_table = UpdateTable.from_dataclass(BronzePrediction)

    query = f"""
    -- Define a CTE to select data once and use it multiple times
    WITH SelectedData AS (
    SELECT
        {payout_table.table_name}.ID as ID,
        {payout_table.table_name}.slot as slot
        {payout_table.table_name}.user as user,
        {payout_table.table_name}.trueval as trueval,
        {payout_table.table_name}.payout as payout,
        {payout_table.table_name}.timestamp as timestamp
    from
        {payout_table.table_name}
    where
        {payout_table.table_name}.timestamp >= {st_ms}
        and {payout_table.table_name}.timestamp < {fin_ms}
    )

    -- We insert the update events into _update_prediction_predctions table
    -- All other params are null.
    INSERT INTO {update_bronze_prediction_table.table_name}
        *.ID as ID,
        *.slot as slot,
        *.user as user,
        *.payout as payout,
        *.timestamp as timestamp
    FROM SelectedData;
    """

    db.create_table_if_not_exists(update_bronze_prediction_table.table_name, BronzePrediction.get_lake_schema())
    db.execute_sql(query)