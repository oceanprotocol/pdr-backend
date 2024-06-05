from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.util.time_types import UnixTimeMS
from pdr_backend.lake.table import NamedTable, EventTable
from pdr_backend.lake.prediction import Prediction
from pdr_backend.lake.table_bronze_pdr_predictions import BronzePrediction

def _do_sql_predictions(
        db:DuckDBDataStore, 
        st_ms: UnixTimeMS, 
        fin_ms: UnixTimeMS ) -> None:
    
    prediction_table = NamedTable.from_dataclass(Prediction)
    event_bronze_prediction_table = EventTable.from_dataclass(BronzePrediction)

    query = f"""
    -- Start a transaction
    BEGIN TRANSACTION;

    -- Define a CTE to select data once and use it multiple times
    WITH SelectedData AS (
    SELECT
        {prediction_table.table_name}.ID as ID,
        "predictoorPrediction" as eventName,
        "new" as eventType,
        SPLIT_PART({prediction_table.table_name}.ID, '-', 1)
            || '-' || SPLIT_PART({prediction_table.table_name}.ID, '-', 2) AS slotID,
        {prediction_table.table_name}.contract,
        {prediction_table.table_name}.slot,
        {prediction_table.table_name}.user,
        {prediction_table.table_name}.pair,
        {prediction_table.table_name}.timeframe,
        {prediction_table.table_name}.source,
        {prediction_table.table_name}.stake,
        {prediction_table.table_name}.predVal,
        {prediction_table.table_name}.timestamp
    from
        {prediction_table.table_name}
    where
        {prediction_table.table_name}.timestamp >= {st_ms}
        and {prediction_table.table_name}.timestamp < {fin_ms}
    )

    INSERT INTO {event_bronze_prediction_table.table_name}
    SELECT * FROM SelectedData;

    -- Commit the transaction
    COMMIT;
    """

    db.create_table_if_not_exists(event_bronze_prediction_table.table_name)
    db.execute_sql(query)