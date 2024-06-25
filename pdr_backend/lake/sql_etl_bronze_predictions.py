from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.util.time_types import UnixTimeMs
from pdr_backend.lake.table import (
    Table,
    NewEventsTable,
    UpdateEventsTable,
    TempUpdateTable,
)
from pdr_backend.lake.table_bronze_pdr_predictions import BronzePrediction


# pylint: disable=unused-argument
def _do_sql_bronze_predictions(
    db: DuckDBDataStore, st_ms: UnixTimeMs, fin_ms: UnixTimeMs
) -> None:
    # historical prediction events
    bronze_prediction_table = Table.from_dataclass(BronzePrediction)

    # new prediction events - to be inserted into prod tables
    new_events_bronze_prediction_table = NewEventsTable.from_dataclass(BronzePrediction)

    # update prediction events - to be joined w/ prod records
    update_events_bronze_prediction_table = UpdateEventsTable.from_dataclass(
        BronzePrediction
    )

    # prod + updated records joined - to be swapped with prod tables
    temp_update_bronze_prediction_table = TempUpdateTable.from_dataclass(
        BronzePrediction
    )

    # df = db.query_data(f"SELECT * FROM {new_events_bronze_prediction_table.table_name}")
    # df.write_csv("pre_query_new_events_bronze_prediction_table.csv")

    # df = db.query_data(
    #     f"SELECT * FROM {update_events_bronze_prediction_table.table_name}"
    # )
    # df.write_csv("pre_query_update_events_bronze_prediction_table.csv")

    query = f"""
    -- Consider that trueval + payout events can happen within seconds from each other
    -- To optimize this whole process we will group update events by ID, and only THEN perform the join
    CREATE TEMPORARY VIEW _update AS
    SELECT
        {update_events_bronze_prediction_table.table_name}.ID,
        null as slot_id,
        null as contract,
        null as slot,
        null as user,
        null as pair,
        null as timeframe,
        null as source,
        MAX({update_events_bronze_prediction_table.table_name}.predvalue) as predvalue,
        MAX({update_events_bronze_prediction_table.table_name}.truevalue) as truevalue,
        MAX({update_events_bronze_prediction_table.table_name}.stake) as stake,
        MAX({update_events_bronze_prediction_table.table_name}.revenue) as revenue,
        MAX({update_events_bronze_prediction_table.table_name}.payout) as payout,
        null as timestamp,
        MAX({update_events_bronze_prediction_table.table_name}.timestamp) as last_event_timestamp
    FROM
        {update_events_bronze_prediction_table.table_name}
    GROUP BY ID;
    
    -- 2. now, we need to update our tables
    -- 2a. first, we're going to enrich the new records that are in the _temp table
    -- These records are ready-to-be-merged and not in prod tables, so, just update their columns.
    UPDATE {new_events_bronze_prediction_table.table_name}
    SET
        predvalue = COALESCE({new_events_bronze_prediction_table.table_name}.predvalue, u.predvalue),
        truevalue = COALESCE({new_events_bronze_prediction_table.table_name}.truevalue, u.truevalue),
        stake = COALESCE({new_events_bronze_prediction_table.table_name}.stake, u.stake),
        revenue = COALESCE({new_events_bronze_prediction_table.table_name}.revenue, u.revenue),
        payout = COALESCE({new_events_bronze_prediction_table.table_name}.payout, u.payout),
        last_event_timestamp = COALESCE(
            {new_events_bronze_prediction_table.table_name}.last_event_timestamp, 
            u.last_event_timestamp
        )
    FROM _update as u
    WHERE {new_events_bronze_prediction_table.table_name}.ID = u.ID;
    """

    # In the first run, there are no historical records
    if db.table_exists(bronze_prediction_table.table_name):
        query += f"""
        -- 2b. Finally join w/ larger historical records from prod table and yield the row to _temp_update table
        -- Step #1 - We can't modify prod table records directly since this would violate atomic properties
        -- Step #2 - Yield updated records into _temp_update table
        -- Step #3 - Use a swap strategy to get _temp_update records into prod table
        INSERT INTO {temp_update_bronze_prediction_table.table_name}
        SELECT
            {bronze_prediction_table.table_name}.ID,
            {bronze_prediction_table.table_name}.slot_id,
            {bronze_prediction_table.table_name}.contract,
            {bronze_prediction_table.table_name}.slot,
            {bronze_prediction_table.table_name}.user,
            {bronze_prediction_table.table_name}.pair,
            {bronze_prediction_table.table_name}.timeframe,
            {bronze_prediction_table.table_name}.source,
            COALESCE(u.predvalue, {bronze_prediction_table.table_name}.predvalue) as predvalue,
            COALESCE(u.truevalue, {bronze_prediction_table.table_name}.truevalue) as truevalue,
            COALESCE(u.stake, {bronze_prediction_table.table_name}.stake) as stake,
            COALESCE(u.revenue, {bronze_prediction_table.table_name}.revenue) as revenue,
            COALESCE(u.payout, {bronze_prediction_table.table_name}.payout) as payout,
            {bronze_prediction_table.table_name}.timestamp,
            GREATEST(
                u.last_event_timestamp,
                {bronze_prediction_table.table_name}.last_event_timestamp
            ) as last_event_timestamp
        FROM _update as u
        INNER JOIN {bronze_prediction_table.table_name}
        ON u.ID = {bronze_prediction_table.table_name}.ID;
        """

    query += """
    -- Drop the view
    DROP VIEW _update;
    """

    db.create_table_if_not_exists(
        temp_update_bronze_prediction_table.table_name,
        BronzePrediction.get_lake_schema(),
    )
    db.execute_sql(query)

    # df = db.query_data(f"SELECT * FROM {temp_bronze_prediction_table.table_name}")
    # df.write_csv("post_query_temp_bronze_prediction_table.csv")

    # df = db.query_data(f"SELECT * FROM {temp_update_bronze_prediction_table.table_name}")
    # df.write_csv("post_query_temp_update_bronze_prediction_table.csv")
