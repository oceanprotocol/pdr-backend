
import polars as pl
from polars import Boolean, Float64, Int64, Utf8

from pdr_backend.lake.table import Table
from pdr_backend.ppss.ppss import PPSS


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

def get_bronze_pdr_predictions_data_with_SQL(ppss: PPSS) -> pl.DataFrame:
    """
    @description
        Get the bronze pdr predictions data
    """
    # get the table
    table = Table(bronze_pdr_predictions_table_name, bronze_pdr_predictions_schema, ppss)

    # process all the data
    return table.PDS.query_data(f"""
        SELECT 
            pdr_predictions.ID as ID,
            string_split(pdr_predictions.ID, '-')[0] AS slot_id,
            pdr_predictions.contract as contract,
            pdr_predictions.slot as slot,
            pdr_predictions.user as user,
            pdr_predictions.pair as pair,
            pdr_predictions.timeframe as timeframe,
            pdr_predictions.source as source,
            pdr_payouts.predvalue as predvalue,
            pdr_truevals.truevalue as truevalue,
            pdr_payouts.stake as stake,
            pdr_payouts.payout as payout,
            pdr_predictions.timestamp as timestamp,
            GREATEST(pdr_predictions.timestamp, pdr_truevals.timestamp, pdr_payouts.timestamp) as last_event_timestamp,
        FROM 
            pdr_predictions
        LEFT JOIN pdr_truevals
            ON pdr_predictions.slot = pdr_truevals.slot                                
        LEFT JOIN pdr_payouts
            ON pdr_predictions.ID = pdr_payouts.ID
        WHERE pdr_predictions.timestamp >= {ppss.lake_ss.st_timestamp}
            AND pdr_predictions.timestamp <= {ppss.lake_ss.fin_timestamp}
    """)
