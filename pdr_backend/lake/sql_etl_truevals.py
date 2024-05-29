# THIS IS QUERY NUMBER 2
process_truevals_query = """
-- Start a transaction
BEGIN TRANSACTION;

-- Define a CTE to select data once and use it multiple times
WITH SelectedData AS (
SELECT
    ID,
    slot,
    "predictoorTrueval" as event_name,
    trueval,
    timestamp
from
    pdr_truevals
where
    pdr_truevals.timestamp >= st_ms
    and pdr_truevals.timestamp < fin_ms
)

-- Insert new records into bronze_truevals
INSERT INTO _temp_bronze_truevals (ID, slot, eventType, eventName, trueval, timestamp)
SELECT
    ID,
    slot,
    "new" as event_type,
    event_name,
    trueval,
    timestamp
FROM SelectedData;

-- DO NOT IMPLEMENT SLOTS TABLE
-- THIS IS JUST AN EXAMPLE OF HOW THIS WILL GROW...
-- Truevals can't be joined w/ user, so we join w/ slots
-- Insert update record into bronze_slots
INSERT INTO _update_temp_bronze_slot (ID, slot, eventType, eventName, stake, trueval, payout, timestamp)
SELECT
    ID,
    slot,
    "update" as event_type,
    event_name,
    null,
    trueval,
    null,
    timestamp
FROM SelectedData;


-- Commit the transaction
COMMIT;
"""