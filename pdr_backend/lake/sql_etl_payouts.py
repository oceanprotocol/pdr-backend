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
    WITH _payout AS (
    SELECT
        {payout_table.fullname}.ID,
        {payout_table.fullname}.slot,
        {payout_table.fullname}.user,
        {payout_table.fullname}.stake,
        {payout_table.fullname}.predvalue,
        {payout_table.fullname}.payout,
        {payout_table.fullname}.timestamp,
    from
        {payout_table.fullname}
    where
        {payout_table.fullname}.timestamp >= {st_ms}
        and {payout_table.fullname}.timestamp < {fin_ms}
    )

    -- We track data we need from payout into _update_prediction_predctions table
    -- All other params are null.
    INSERT INTO {update_bronze_prediction_table.fullname}
    SELECT 
        p.ID,
        SPLIT_PART(p.ID, '-', 1)
            || '-' || SPLIT_PART(p.ID, '-', 2) AS slot_id,
        null as contract,
        p.slot,
        p.user,
        null as pair,
        null as timeframe,
        null as source,
        p.predvalue,
        null as truevalue,
        p.stake,
        -- do not use revenue from payout, it's not correct
        null as revenue,
        p.payout,
        p.timestamp,
        p.timestamp as last_event_timestamp
    FROM _payout as p;
    """

    db.create_table_if_not_exists(update_bronze_prediction_table.fullname, BronzePrediction.get_lake_schema())
    db.execute_sql(query)

    # df = db.query_data(f"SELECT * FROM {payout_table.fullname}")
    # df.write_csv(f"{payout_table.fullname}.csv")