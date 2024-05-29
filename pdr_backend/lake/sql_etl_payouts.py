# THIS IS QUERY NUMBER 3
process_payouts_query = """
-- Start a transaction
BEGIN TRANSACTION;

-- Define a CTE to select data once and use it multiple times
WITH SelectedData AS (
SELECT
    ID as ID,
    "predictoorPayout" as event_name,
    user as user,
    trueval as trueval,
    payout as payout,
    timestamp as timestamp
    slot as slot
from
    pdr_payouts
where
    pdr_payouts.timestamp >= st_ms
    and pdr_payouts.timestamp < fin_ms
)

-- Insert into the first table using the CTE
INSERT INTO _temp_bronze_payouts (ID, slot, eventType, eventName, user, trueval, payout, timestamp)
SELECT
    ID as ID,
    "new" as event_type,
    user as user,
    trueval as trueval,
    payout as payout,
    timestamp as timestamp
    slot as slot
FROM SelectedData;

-- We insert the update event data into _update_bronze_predctions table
-- All other params are null.
INSERT INTO _update_bronze_predictions (ID, slot, eventType, eventName, user, trueval, payout, timestamp, slot)
    slot_ID as slot_ID,
    ID as ID,
    "update" as event_type,
    user as user,
    null as trueval,
    payout as payout,
    timestamp as timestamp
    slot as slot
FROM SelectedData;

-- Commit the transaction
COMMIT;
"""