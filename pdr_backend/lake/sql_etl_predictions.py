from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.util.time_types import UnixTimeMs
from pdr_backend.lake.table import NamedTable, TempTable
from pdr_backend.lake.prediction import Prediction
from pdr_backend.lake.table_bronze_pdr_predictions import BronzePrediction

def _do_sql_predictions(
        db: DuckDBDataStore, 
        st_ms: UnixTimeMs, 
        fin_ms: UnixTimeMs ) -> None:
    
    prediction_table = NamedTable.from_dataclass(Prediction)
    temp_bronze_prediction_table = TempTable.from_dataclass(BronzePrediction)

    query = f"""
    -- Define a CTE to select data once and use it multiple times
    WITH _predictions AS (
    SELECT
        {prediction_table.fullname}.ID,
        SPLIT_PART({prediction_table.fullname}.ID, '-', 1)
            || '-' || SPLIT_PART({prediction_table.fullname}.ID, '-', 2) AS slot_id,
        {prediction_table.fullname}.contract,
        {prediction_table.fullname}.slot,
        {prediction_table.fullname}.user,
        {prediction_table.fullname}.pair,
        {prediction_table.fullname}.timeframe,
        {prediction_table.fullname}.source,
        -- don't cheat, verify we can recreate subgraph
        null as predvalue,
        null as truevalue,
        null as stake,
        null as revenue,
        null as payout,
        {prediction_table.fullname}.timestamp,
        {prediction_table.fullname}.timestamp as last_event_timestamp,
    from
        {prediction_table.fullname}
    where
        {prediction_table.fullname}.timestamp >= {st_ms}
        and {prediction_table.fullname}.timestamp < {fin_ms}
    )

    INSERT INTO {temp_bronze_prediction_table.fullname}
    SELECT 
        * 
    FROM _predictions as p;
    """

    db.create_table_if_not_exists(temp_bronze_prediction_table.fullname, BronzePrediction.get_lake_schema())
    db.execute_sql(query)
