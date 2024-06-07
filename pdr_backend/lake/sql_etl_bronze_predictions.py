from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.util.time_types import UnixTimeMs
from pdr_backend.lake.table import UpdateTable, TempUpdateTable
from pdr_backend.lake.table_bronze_pdr_predictions import BronzePrediction

def _do_sql_bronze_predictions(
        db:DuckDBDataStore, 
        st_ms: UnixTimeMs, 
        fin_ms: UnixTimeMs ) -> None:
    
    # new prediction events - to be inserted into prod tables
    update_bronze_prediction_table = UpdateTable.from_dataclass(BronzePrediction)

    # update prediction events - to be joined w/ prod records
    update_bronze_prediction_table = UpdateTable.from_dataclass(BronzePrediction)
    
    # prod + updated records joined - to be swapped with prod tables
    temp_update_bronze_prediction_table = TempUpdateTable.from_dataclass(BronzePrediction)

    query = f"""
    -- Start a transaction
    BEGIN TRANSACTION;

    -- 1. let's group all update events by ID to reduce into a single row
    WITH UpdatedRows AS (
    SELECT
        *,
        MIN(timestamp) as timestamp,
        MAX(trueval) AS trueval,
        MAX(payout) AS payout,
        MAX(timestamp) AS lastEventTimestamp,
    FROM
        {update_bronze_prediction_table.table_name}
    GROUP BY ID

    -- 2. now, we need to update our tables
    -- 2a. update any records that may be in the _temp table, already to-be-merged
    -- Because these records are not in the live table, we can just update their columns.
    UPDATE {temp_update_bronze_prediction_table.table_name}
    SET
        trueval = COALESCE(UpdatedRows.trueval, live_table.trueval),
        payout = COALESCE(UpdatedRows.payout, live_table.payout),
        timestamp = UpdatedRows.lastEventTimestamp,
        slot = UpdatedRows.slot
    FROM UpdatedRows
    WHERE live_table.ID = UpdatedRows.ID;

    -- 2b. Join w/ existing records and yield the row to _temp_update table
    -- Step #1 - Because these records are from the live table, we can't modify them
    -- Step #2 - Yield updated records into _temp_update table
    -- Step #3 - Use a swap strategy to get _temp_update records into prod table
    INSERT INTO _temp_update_bronze_predictions
    SELECT
        *{temp_update_bronze_prediction_table.table_name},
        COALESCE(UpdatedRows.trueval, {temp_update_bronze_prediction_table.table_name}.trueval) as trueval,
        COALESCE(UpdatedRows.payout, {temp_update_bronze_prediction_table.table_name}.payout) as payout,
        MAX(UpdatedRows.lastEventTimestamp, {temp_update_bronze_prediction_table.table_name}.lastEventTimestamp) as lastEventTimestamp)
    FROM UpdatedRows
    LEFT JOIN {temp_update_bronze_prediction_table.table_name}
    ON UpdatedRows.ID = {temp_update_bronze_prediction_table.table_name}.ID

    -- Commit the transaction
    COMMIT;
    """

    db.create_table_if_not_exists(temp_update_bronze_prediction_table.table_name)
    db.execute_sql(query)
