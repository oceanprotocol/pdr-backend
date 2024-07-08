from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.util.time_types import UnixTimeMs
from pdr_backend.lake.table import Table, UpdateEventsTable
from pdr_backend.lake.payout import Payout
from pdr_backend.lake.table_bronze_pdr_predictions import BronzePrediction


def _do_sql_payouts(
    db: DuckDBDataStore, st_ms: UnixTimeMs, fin_ms: UnixTimeMs, first_run: bool = False
) -> None:
    payout_table = Table.from_dataclass(Payout)
    update_events_bronze_prediction_table = UpdateEventsTable.from_dataclass(
        BronzePrediction
    )

    st_ms_conditional_check = ">=" if first_run else ">"

    query = f"""
    -- Define a CTE to select data once and use it multiple times
    WITH _payout AS (
    SELECT
        {payout_table.table_name}.ID,
        {payout_table.table_name}.slot,
        {payout_table.table_name}.user,
        {payout_table.table_name}.predvalue,
        {payout_table.table_name}.stake,
        {payout_table.table_name}.payout,
        {payout_table.table_name}.timestamp,
    from
        {payout_table.table_name}
    where
        {payout_table.table_name}.timestamp {st_ms_conditional_check} {st_ms}
        and {payout_table.table_name}.timestamp <= {fin_ms}
    )

    -- We track data we need from payout into _update_prediction_predctions table
    -- All other params are null.
    INSERT INTO {update_events_bronze_prediction_table.table_name}
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

    db.create_table_if_not_exists(
        update_events_bronze_prediction_table.table_name,
        BronzePrediction.get_lake_schema(),
    )
    db.execute_sql(query)
