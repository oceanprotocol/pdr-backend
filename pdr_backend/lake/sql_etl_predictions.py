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

-- DO NOT IMPLEMENT SLOTS TABLE
-- THIS IS JUST AN EXAMPLE OF HOW THIS WILL GROW...
-- Insert update record into bronze_slots
INSERT INTO _update_temp_bronze_slot (ID, slot, eventType, eventName, stake, trueval, payout, timestamp)
SELECT
    ID,
    slot,
    "update" as event_type,
    event_name,
    stake,
    null,
    null,
    timestamp
FROM SelectedData;

-- Commit the transaction
COMMIT;
"""