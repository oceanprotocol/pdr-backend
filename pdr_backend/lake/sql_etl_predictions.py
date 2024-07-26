from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.util.time_types import UnixTimeMs
from pdr_backend.lake.table import Table, NewEventsTable
from pdr_backend.lake.prediction import Prediction
from pdr_backend.lake.table_bronze_pdr_predictions import BronzePrediction


def _do_sql_predictions(
    db: DuckDBDataStore, st_ms: UnixTimeMs, fin_ms: UnixTimeMs, first_run: bool = False
) -> None:
    prediction_table = Table.from_dataclass(Prediction)
    new_events_bronze_prediction_table = NewEventsTable.from_dataclass(BronzePrediction)

    st_ms_conditional_check = ">=" if first_run else ">"

    query = f"""
    -- Define a CTE to select data once and use it multiple times
    WITH _predictions AS (
    SELECT
        {prediction_table.table_name}.ID,
        SPLIT_PART({prediction_table.table_name}.ID, '-', 1)
            || '-' || SPLIT_PART({prediction_table.table_name}.ID, '-', 2) AS slot_id,
        {prediction_table.table_name}.contract,
        {prediction_table.table_name}.slot,
        {prediction_table.table_name}.user,
        {prediction_table.table_name}.pair,
        {prediction_table.table_name}.timeframe,
        {prediction_table.table_name}.source,
        -- don't cheat, verify we can recreate subgraph
        null as predvalue,
        null as truevalue,
        null as stake,
        null as revenue,
        null as payout,
        {prediction_table.table_name}.timestamp,
        {prediction_table.table_name}.timestamp as last_event_timestamp,
    from
        {prediction_table.table_name}
    where
        {prediction_table.table_name}.timestamp {st_ms_conditional_check} {st_ms}
        and {prediction_table.table_name}.timestamp <= {fin_ms}
    )

    INSERT INTO {new_events_bronze_prediction_table.table_name}
    SELECT 
        * 
    FROM _predictions as p;
    """

    db.create_empty(
        new_events_bronze_prediction_table.table_name,
        BronzePrediction.get_lake_schema(),
    )
    db.execute_sql(query)
