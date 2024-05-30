# THIS IS QUERY NUMBER 1
process_predictions_query = """
-- Start a transaction
BEGIN TRANSACTION;

-- Define a CTE to select data once and use it multiple times
WITH SelectedData AS (
SELECT
    ID,
    slot,
    "predictoorPrediction" as event_name,
    user,
    stake,
    predVal,
    timestamp
from
    pdr_predictions
where
    pdr_predictions.timestamp >= st_ms
    and pdr_predictions.timestamp < fin_ms
)

-- Insert new records into bronze_predictions
INSERT INTO _temp_bronze_predictions (ID, slot, eventType, eventName, user, stake, predval, trueval, payout, timestamp)
SELECT
    ID,
    slot,
    "new" as event_type,
    event_name,
    user,
    stake,
    predVal,
    null,
    null,
    timestamp
FROM SelectedData;

-- Commit the transaction
COMMIT;
"""

def _process_predictions_query(
    path=self.ppss.lake_ss.lake_dir,
    st_ms=st_timestamp,
    fin_ms=fin_timestamp):
    
    db = DuckDBDataStore(path)
    
    db.create_table_if_not_exists("_temp_bronze_predictions")    
    db.execute_sql(process_predictions_query)
