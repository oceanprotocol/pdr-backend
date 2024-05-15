import logging
from collections import OrderedDict

from enforce_typing import enforce_types
from polars import Boolean, Float64, Int64, Utf8

from pdr_backend.lake.payout import Payout
from pdr_backend.lake.persistent_data_store import PersistentDataStore
from pdr_backend.lake.slot import Slot
from pdr_backend.lake.table import ETLTable, NamedTable, TempTable
from pdr_backend.lake.table_bronze_pdr_predictions import BronzePrediction
from pdr_backend.lake.trueval import Trueval
from pdr_backend.util.time_types import UnixTimeMs

logger = logging.getLogger("lake")


# CLEAN & ENRICHED PREDICTOOR SLOTS SCHEMA
class BronzeSlot:
    @staticmethod
    def get_lake_schema():
        return OrderedDict(
            {
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
        )

    @staticmethod
    def get_lake_table_name():
        return "bronze_pdr_slots"


@enforce_types
def get_bronze_pdr_slots_data_with_SQL(
    path: str, st_ms: UnixTimeMs, fin_ms: UnixTimeMs
):
    pdr_slots_table_name = NamedTable.from_dataclass(Slot).fullname
    pdr_truevals_table_name = NamedTable.from_dataclass(Trueval).fullname
    pdr_payouts_table_name = NamedTable.from_dataclass(Payout).fullname
    etl_bronze_pdr_predictions_table_name = ETLTable.from_dataclass(
        BronzePrediction
    ).fullname
    temp_bronze_pdr_slots_table_name = TempTable.from_dataclass(BronzeSlot).fullname

    pds = PersistentDataStore(path)

    pds.create_table_if_not_exists(
        temp_bronze_pdr_slots_table_name, BronzeSlot.get_lake_schema()
    )

    query = f"""
            INSERT INTO {temp_bronze_pdr_slots_table_name}
            SELECT DISTINCT
                {pdr_slots_table_name}.ID AS ID,
                SPLIT_PART({pdr_slots_table_name}.ID, '-', 1) AS contract,
                joined_{etl_bronze_pdr_predictions_table_name}.pair AS pair,
                joined_{etl_bronze_pdr_predictions_table_name}.timeframe AS timeframe,
                joined_{etl_bronze_pdr_predictions_table_name}.source AS source,
                {pdr_slots_table_name}.slot AS slot,
                joined_{pdr_payouts_table_name}.roundSumStakesUp AS roundSumStakesUp,
                joined_{pdr_payouts_table_name}.roundSumStakes AS roundSumStakes,
                {pdr_truevals_table_name}.truevalue AS truevalue,
                {pdr_slots_table_name}.timestamp AS timestamp,
                GREATEST(
                    {pdr_slots_table_name}.timestamp,
                    {pdr_truevals_table_name}.timestamp,
                    joined_{pdr_payouts_table_name}.timestamp,
                    joined_{etl_bronze_pdr_predictions_table_name}.timestamp
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
            ) AS joined_{etl_bronze_pdr_predictions_table_name} ON {pdr_slots_table_name}.ID = joined_{etl_bronze_pdr_predictions_table_name}.slot_id
            LEFT JOIN (
                SELECT
                    SPLIT_PART(ID, '-', 1) || '-' || SPLIT_PART(ID, '-', 2) AS slot_id,
                    MAX(roundSumStakesUp) AS roundSumStakesUp,
                    MAX(roundSumStakes) AS roundSumStakes,
                    MAX(timestamp) AS timestamp
                FROM {pdr_payouts_table_name}
                GROUP BY slot_id
            ) AS joined_{pdr_payouts_table_name} ON {pdr_slots_table_name}.ID = joined_{pdr_payouts_table_name}.slot_id
            WHERE
                pdr_slots.timestamp > {st_ms}
                AND pdr_slots.timestamp <= {fin_ms}
            ORDER BY timestamp
        """

    logger.info("table_bronze_slot_query %s", query)

    return pds.execute_sql(query)
