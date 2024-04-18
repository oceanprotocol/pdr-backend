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
            SELECT
                {pdr_slots_table_name}.ID as ID,
                SPLIT_PART({pdr_slots_table_name}.ID, '-', 1) as contract,
                {etl_bronze_pdr_predictions_table_name}.pair as pair,
                {etl_bronze_pdr_predictions_table_name}.timeframe as timeframe,
                {etl_bronze_pdr_predictions_table_name}.source as source,
                {pdr_slots_table_name}.slot as slot,
                {pdr_slots_table_name}.timestamp as timestamp,
                {pdr_payouts_table_name}.roundSumStakesUp as roundSumStakesUp,
                {pdr_payouts_table_name}.roundSumStakes as roundSumStakes,
                {pdr_truevals_table_name}.truevalue as truevalue,
                GREATEST(
                    {pdr_slots_table_name}.timestamp,
                    {pdr_payouts_table_name}.timestamp,
                    {etl_bronze_pdr_predictions_table_name}.timestamp,
                    {pdr_truevals_table_name}.timestamp
                ) as last_event_timestamp,
            FROM
                {pdr_slots_table_name}
            LEFT JOIN {pdr_payouts_table_name}
            ON {pdr_slots_table_name}.ID = SPLIT_PART({pdr_payouts_table_name}.ID, '-', 1)
                || '-' || SPLIT_PART({pdr_payouts_table_name}.ID, '-', 2)
            LEFT JOIN {pdr_truevals_table_name}
            ON {pdr_slots_table_name}.ID = {pdr_truevals_table_name}.ID
            LEFT JOIN {etl_bronze_pdr_predictions_table_name}
            ON {pdr_slots_table_name}.ID = {etl_bronze_pdr_predictions_table_name}.slot_id
            WHERE
                {pdr_slots_table_name}.timestamp >= {st_ms}
                AND {pdr_slots_table_name}.timestamp <= {fin_ms}
        """

    logger.info("table_bronze_slot_query %s", query)

    return pds.execute_sql(query)
