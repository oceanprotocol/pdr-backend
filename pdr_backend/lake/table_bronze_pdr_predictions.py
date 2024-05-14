import logging
from collections import OrderedDict

from polars import Boolean, Float64, Int64, Utf8

from pdr_backend.lake.persistent_data_store import PersistentDataStore
from pdr_backend.lake.table import NamedTable, TempTable
from pdr_backend.util.time_types import UnixTimeMs

logger = logging.getLogger("lake")


# CLEAN & ENRICHED PREDICTOOR PREDICTIONS SCHEMA
class BronzePrediction:
    @staticmethod
    def get_lake_schema():
        return OrderedDict(
            {
                "ID": Utf8,  # f"{contract}-{slot}-{user}"
                "slot_id": Utf8,  # f"{contract}-{slot}"
                "contract": Utf8,  # f"{contract}"
                "slot": Int64,
                "user": Utf8,
                "pair": Utf8,
                "timeframe": Utf8,
                "source": Utf8,
                "predvalue": Boolean,
                "truevalue": Boolean,
                "stake": Float64,
                "payout": Float64,
                "timestamp": Int64,
                "last_event_timestamp": Int64,
            }
        )

    @staticmethod
    def get_lake_table_name():
        return "bronze_pdr_predictions"


def get_bronze_pdr_predictions_data_with_SQL(
    path: str, st_ms: UnixTimeMs, fin_ms: UnixTimeMs
):
    """
    @description
        Get the bronze pdr predictions data
    """
    pdr_predictions_table_name = NamedTable("pdr_predictions").fullname
    pdr_truevals_table_name = NamedTable("pdr_truevals").fullname
    pdr_payouts_table_name = NamedTable("pdr_payouts").fullname
    temp_bronze_pdr_predictions_table_name = TempTable.from_dataclass(
        BronzePrediction
    ).fullname

    pds = PersistentDataStore(path)
    logger.info("pds tables %s", pds.get_table_names())

    pds.create_table_if_not_exists(
        temp_bronze_pdr_predictions_table_name,
        BronzePrediction.get_lake_schema(),
    )

    return pds.execute_sql(
        f"""
        INSERT INTO {temp_bronze_pdr_predictions_table_name}
        SELECT
            {pdr_predictions_table_name}.ID as ID,
            SPLIT_PART({pdr_predictions_table_name}.ID, '-', 1)
                || '-' || SPLIT_PART({pdr_predictions_table_name}.ID, '-', 2) AS slot_id,
            {pdr_predictions_table_name}.contract as contract,
            {pdr_predictions_table_name}.slot as slot,
            {pdr_predictions_table_name}.user as user,
            {pdr_predictions_table_name}.pair as pair,
            {pdr_predictions_table_name}.timeframe as timeframe,
            {pdr_predictions_table_name}.source as source,
            {pdr_payouts_table_name}.predvalue as predvalue,
            {pdr_truevals_table_name}.truevalue as truevalue,
            {pdr_payouts_table_name}.stake as stake,
            {pdr_payouts_table_name}.payout as payout,
            {pdr_predictions_table_name}.timestamp as timestamp,
            GREATEST({pdr_predictions_table_name}.timestamp,
                {pdr_truevals_table_name}.timestamp, {pdr_payouts_table_name}.timestamp)
                as last_event_timestamp,
        FROM
            {pdr_predictions_table_name}
        LEFT JOIN {pdr_truevals_table_name}
            ON {pdr_predictions_table_name}.slot = {pdr_truevals_table_name}.slot
            AND {pdr_predictions_table_name}.contract =
                SPLIT_PART({pdr_truevals_table_name}.ID, '-', 1)
        LEFT JOIN {pdr_payouts_table_name}
            ON {pdr_predictions_table_name}.ID = {pdr_payouts_table_name}.ID
        WHERE {pdr_predictions_table_name}.timestamp >= {st_ms}
            AND {pdr_predictions_table_name}.timestamp <= {fin_ms}
    """
    )
