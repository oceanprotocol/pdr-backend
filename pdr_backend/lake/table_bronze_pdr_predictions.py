import polars as pl
from polars import Boolean, Float64, Int64, Utf8

from pdr_backend.lake.persistent_data_store import PersistentDataStore
from pdr_backend.lake.table import get_table_name
from pdr_backend.util.time_types import UnixTimeMs

bronze_pdr_predictions_table_name = "bronze_pdr_predictions"

# CLEAN & ENRICHED PREDICTOOR PREDICTIONS SCHEMA
bronze_pdr_predictions_schema = {
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


def get_bronze_pdr_predictions_data_with_SQL(
    path: str, st_ms: UnixTimeMs, fin_ms: UnixTimeMs
) -> pl.DataFrame:
    """
    @description
        Get the bronze pdr predictions data
    """
    pdr_predictions_table_name = get_table_name("pdr_predictions")
    pdr_truevals_table_name = get_table_name("pdr_truevals")
    pdr_payouts_table_name = get_table_name("pdr_payouts")

    pds = PersistentDataStore(path)
    print(f"pds tables {pds.get_table_names()}")

    return pds.query_data(
        f"""
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
        LEFT JOIN {pdr_payouts_table_name}
            ON {pdr_predictions_table_name}.ID = {pdr_payouts_table_name}.ID
        WHERE {pdr_predictions_table_name}.timestamp >= {st_ms}
            AND {pdr_predictions_table_name}.timestamp <= {fin_ms}
    """
    )
