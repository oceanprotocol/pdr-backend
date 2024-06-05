from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.util.time_types import UnixTimeMS
from pdr_backend.lake.table import NamedTable, TempTable, ETLTable, EventTable
from pdr_backend.lake.payout import Payout
from pdr_backend.lake.prediction import Prediction
from pdr_backend.lake.table_bronze_pdr_predictions import BronzePrediction

def _do_sql_bronze_predictions(
        db:DuckDBDataStore, 
        st_ms: UnixTimeMS, 
        fin_ms: UnixTimeMS ) -> None:
    
    update_bronze_prediction_table = EventTable.from_dataclass(BronzePrediction)
    temp_bronze_prediction_table = EventTable.from_dataclass(BronzePrediction)

    query = f"""
    -- Start a transaction
    BEGIN TRANSACTION;

    -- 1. let's group all update events by ID, to reduce multiples
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

    -- 2. now update _temp table
    UPDATE {temp_bronze_prediction_table.table_name}
    SET
        trueval = COALESCE(UpdatedRows.trueval, live_table.trueval),
        payout = COALESCE(UpdatedRows.payout, live_table.payout),
        timestamp = UpdatedRows.lastEventTimestamp,
        slot = UpdatedRows.slot
    FROM UpdatedRows
    WHERE live_table.ID = UpdatedRows.ID;

    -- 3. now insert into _temp_update
    # 1. WE'RE GOING TO NOW, FINALLY, AND ONLY ONCE, JOIN WITH THE ETL BRONZE_TABLE
    # 2. We're going to then insert into _temp_update table
    # 3. _temp_update will have a different merge strategy
    INSERT INTO _temp_update_bronze_predictions
    SELECT
        *{temp_bronze_prediction_table.table_name},
        lastEventTimestamp
    FROM UpdatedRows
    LEFT JOIN {temp_bronze_prediction_table.table_name}
    ON UpdatedRows.ID = {temp_bronze_prediction_table.table_name}.ID

    -- Commit the transaction
    COMMIT;
    """

    db.create_table_if_not_exists(update_bronze_prediction_table.table_name)
    db.execute_sql(query)
