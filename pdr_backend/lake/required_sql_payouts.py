# THIS IS QUERY NUMBER 2
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

-- We insert the update event data into _update_bronze_predctions table
-- All other params are null.
INSERT INTO _update_predictions (ID, slot, eventType, eventName, user, trueval, payout, timestamp, slot)
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

def _process_predictions_query(
    path=self.ppss.lake_ss.lake_dir,
    st_ms=st_timestamp,
    fin_ms=fin_timestamp):
    
    db = DuckDBDataStore(path)
    
    db.create_table_if_not_exists("_update_predictions")    
    db.execute_sql(process_payouts_query)