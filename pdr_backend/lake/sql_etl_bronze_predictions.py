process_bronze_predictions_query = """
-- Start a transaction
BEGIN TRANSACTION;

-- Do all the calculations required when grouping update events
-- Sum/Count/Max/Min/GroupBy/Where/Case/When/Then/Else
WITH UpdatedRows AS (
    SELECT 
        ID,
        ...,
        MAX(trueval) AS trueval,  -- Assumes only one non-null trueval per ID
        MAX(payout) AS payout,  -- Assumes only one non-null payout per ID
        ...,
    FROM _update_bronze_predictions
    GROUP BY ID
)

# 1. WE'RE GOING TO NOW, FINALLY, AND ONLY ONCE, JOIN WITH THE ETL BRONZE_TABLE
# 2. We're going to insert into _temp_update table so we can finalize the records
INSERT INTO _temp_update_bronze_predictions (
    ID, 
    eventType, 
    eventName, 
    user, 
    trueval, 
    payout, 
    timestamp, 
    slot,
    ...
) SELECT
    ID as ID,
    "new" as event_type,
    user as user,
    payout as payout,
    timestamp as timestamp
    slot as slot
FROM SelectedData;

# Insert into the second table using the CTE
# DO NOT IMPLEMENT SLOTS TABLE - THIS IS JUST AN EXAMPLE...
INSERT INTO _update_bronze_slot (ID, eventType, eventName, user, payout, timestamp, slot)
SELECT
    ID as ID,
    "update" as event_type,
    "predictoorPrediction" as event_name,
    user as user,
    payout as payout,
    timestamp as timestamp
    slot as slot
FROM SelectedData;

-- Commit the transaction
COMMIT;
"""
