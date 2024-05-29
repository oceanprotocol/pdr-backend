# THIS IS QUERY NUMBER 3
process_bronze_predictions_query = """
-- Start a transaction
BEGIN TRANSACTION;

-- We now want to "reduce" or "coalesce the rows" by grouping by the ID
WITH UpdatedRows AS (
    SELECT 
        ID,
        ...,
        MAX(trueval) AS trueval,  -- Assumes only one non-null trueval per ID
        MAX(payout) AS payout,  -- Assumes only one non-null payout per ID
        ...,
    FROM _update_predictions
    GROUP BY ID
    ORDER BY ID, TIMESTAMP
)

# 1. WE'RE GOING TO NOW, FINALLY, AND ONLY ONCE, JOIN WITH THE ETL BRONZE_TABLE
# 2. We're going to insert into _temp_update table so we can finalize the records
INSERT INTO _update_bronze_predictions (
    _etl_bronze_predictions.ID, 
    _etl_bronze_predictions...,
    UpdatedData.payout not null and _etl_bronze_predictions.payout null then UpdatedData.payout else _etl_bronze_predictions.payout end as payout,
    UpdatedData.trueval not null and _etl_bronze_predictions.trueval null then UpdatedData.trueval else _etl_bronze_predictions.trueval end as trueval,
    UpdatedData.eventType as lastEventType,
    UpdatedData.eventName as lastEventName,
    _etl_bronze_predictions...,
) SELECT
    ID as ID,
    "new" as event_type,
    user as user,
    payout as payout,
    timestamp as timestamp
    slot as slot
FROM UpdatedData
LEFT JOIN _etl_bronze_predictions
on UpdatedData.ID = _etl_bronze_predictions.ID

-- Commit the transaction
COMMIT;
"""

def _process_bronze_predictions_query(
    path=self.ppss.lake_ss.lake_dir,
    st_ms=st_timestamp,
    fin_ms=fin_timestamp):
    
    db = DuckDBDataStore(path)
    
    db.create_table_if_not_exists("_update_bronze_predictions")    
    db.execute_sql(process_bronze_predictions_query)