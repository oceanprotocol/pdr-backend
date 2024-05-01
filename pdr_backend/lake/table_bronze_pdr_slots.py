import logging
from enforce_typing import enforce_types
from polars import Boolean, Float64, Int64, Utf8

from pdr_backend.util.time_types import UnixTimeMs
from pdr_backend.lake.table import get_table_name, TableType
from pdr_backend.lake.persistent_data_store import PersistentDataStore
from pdr_backend.lake.table_pdr_slots import slots_table_name
from pdr_backend.lake.table_pdr_truevals import truevals_table_name
from pdr_backend.lake.table_pdr_payouts import payouts_table_name
from pdr_backend.lake.table_bronze_pdr_predictions import (
    bronze_pdr_predictions_table_name,
)

logger = logging.getLogger("lake")
bronze_pdr_slots_table_name = "bronze_pdr_slots"

# CLEAN & ENRICHED PREDICTOOR SLOTS SCHEMA
bronze_pdr_slots_schema = {
    "ID": Utf8,  # f"{contract}-{slot}"
    "contract": Utf8,  # f"{contract}"
    "pair": Utf8,
    "timeframe": Utf8,
    "source": Utf8,
    "slot": Int64,
    "roundSumStakesUp": Float64,
    "roundSumStakes": Float64,
    "truevalue": Boolean,
    "timestamp": Int64,
    "last_event_timestamp": Int64,
}


@enforce_types
def get_bronze_pdr_slots_data_with_SQL(
    path: str, st_ms: UnixTimeMs, fin_ms: UnixTimeMs
):
    pdr_slots_table_name = get_table_name(slots_table_name)
    pdr_truevals_table_name = get_table_name(truevals_table_name)
    pdr_payouts_table_name = get_table_name(payouts_table_name)
    etl_bronze_pdr_predictions_table_name = get_table_name(
        bronze_pdr_predictions_table_name, TableType.ETL
    )
    temp_bronze_pdr_slots_table_name = get_table_name(
        bronze_pdr_slots_table_name, TableType.TEMP
    )

    pds = PersistentDataStore(path)

    pds.create_table_if_not_exists(
        temp_bronze_pdr_slots_table_name,
        bronze_pdr_slots_schema,
    )

    query = f"""
            INSERT INTO {temp_bronze_pdr_slots_table_name}
            SELECT DISTINCT
                {pdr_slots_table_name}.ID AS ID,
                SPLIT_PART({pdr_slots_table_name}.ID, '-', 1) AS contract,
                {etl_bronze_pdr_predictions_table_name}.pair AS pair,
                {etl_bronze_pdr_predictions_table_name}.timeframe AS timeframe,
                {etl_bronze_pdr_predictions_table_name}.source AS source,
                {pdr_slots_table_name}.slot AS slot,
                {pdr_payouts_table_name}.roundSumStakesUp AS roundSumStakesUp,
                {pdr_payouts_table_name}.roundSumStakes AS roundSumStakes,
                {pdr_truevals_table_name}.truevalue AS truevalue,
                {pdr_slots_table_name}.timestamp AS timestamp,
                GREATEST(
                    {pdr_slots_table_name}.timestamp,
                    {pdr_truevals_table_name}.timestamp,
                    {pdr_payouts_table_name}.timestamp,
                    {etl_bronze_pdr_predictions_table_name}.timestamp
                ) AS last_event_timestamp
            FROM
                {pdr_slots_table_name}
            LEFT JOIN {pdr_truevals_table_name} ON {pdr_slots_table_name}.ID = {pdr_truevals_table_name}.ID
            LEFT JOIN (
                SELECT 
                    {pdr_slots_table_name}.ID AS slot_id,
                    MAX({etl_bronze_pdr_predictions_table_name}.pair) AS pair,
                    MAX({etl_bronze_pdr_predictions_table_name}.timeframe) AS timeframe,
                    MAX({etl_bronze_pdr_predictions_table_name}.source) AS source,
                    MAX({etl_bronze_pdr_predictions_table_name}.timestamp) AS timestamp
                FROM {pdr_slots_table_name}
                LEFT JOIN {etl_bronze_pdr_predictions_table_name} ON SPLIT_PART({pdr_slots_table_name}.ID, '-', 1) = {etl_bronze_pdr_predictions_table_name}.contract
                GROUP BY {pdr_slots_table_name}.ID
            ) AS {etl_bronze_pdr_predictions_table_name} ON {pdr_slots_table_name}.ID = {etl_bronze_pdr_predictions_table_name}.slot_id
            LEFT JOIN (
                SELECT 
                    SPLIT_PART(ID, '-', 1) || '-' || SPLIT_PART(ID, '-', 2) AS slot_id,
                    MAX(roundSumStakesUp) AS roundSumStakesUp,
                    MAX(roundSumStakes) AS roundSumStakes,
                    MAX(timestamp) AS timestamp
                FROM {pdr_payouts_table_name}
                GROUP BY slot_id
            ) AS {pdr_payouts_table_name} ON {pdr_slots_table_name}.ID = {pdr_payouts_table_name}.slot_id
            WHERE
                {pdr_slots_table_name}.timestamp >= {st_ms}
                AND {pdr_slots_table_name}.timestamp <= {fin_ms}
            ORDER BY timestamp
        """

    logger.info("table_bronze_slot_query %s", query)

    return pds.execute_sql(query)
