import logging
from collections import OrderedDict

from polars import Boolean, Float64, Int64, Utf8

from pdr_backend.lake.lake_mapper import LakeMapper
from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.lake.table import NamedTable, TempTable
from pdr_backend.util.time_types import UnixTimeMs
from pdr_backend.lake.table import TableType
logger = logging.getLogger("lake")


# CLEAN & ENRICHED PREDICTOOR PREDICTIONS SCHEMA
class BronzePrediction(LakeMapper):
    def __init__(self):
        super().__init__()
        self.check_against_schema()

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

    db = DuckDBDataStore(path)
    logger.info("duckDB tables %s", db.get_table_names())

    db.create_table_if_not_exists(
        temp_bronze_pdr_predictions_table_name,
        BronzePrediction.get_lake_schema(),
    )

    return db.execute_sql(
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
        WHERE {pdr_predictions_table_name}.timestamp > {st_ms}
            AND {pdr_predictions_table_name}.timestamp <= {fin_ms}
    """
    )

def update_bronze_predictions(
    path: str, st_ms: UnixTimeMs, fin_ms: UnixTimeMs
):
    """
    @description
        Update the bronze predictions table with the latest data
        
    @param
        path: str: path to the duckdb database
        st_ms: UnixTimeMs: start timestamp in milliseconds
        fin_ms: UnixTimeMs: finish timestamp in milliseconds
    """


    # GET THE TABLE NAMES
    bronze_prediction_table = NamedTable(BronzePrediction.get_lake_table_name()).fullname
    update_prediction_table = NamedTable(BronzePrediction.get_lake_table_name(), TableType.UPDATE).fullname,

    # Initialize the duckdb database (get the instance)
    db = DuckDBDataStore(path)

    # Check if the bronze prediction table exists
    if db.table_exists(bronze_prediction_table) is False:
        return
       
    # CREATE THE UPDATE PREDICTION TABLE, IF IT EXISTS DROP IT
    if db.table_exists(update_prediction_table) is True:
        db.drop_table(update_prediction_table)

    # COPY THE BRONZE PREDICTION TABLE TO THE UPDATE PREDICTION TABLE
    db.copy_table(
        source_table_name=bronze_prediction_table,
        target_table_name=update_prediction_table,
        with_data=False,
    )

    # GET THE TABLE NAMES for the data
    pdr_truevals_table_name = NamedTable("pdr_truevals").fullname
    pdr_payouts_table_name = NamedTable("pdr_payouts").fullname

    # INSERT THE DATA INTO THE UPDATE PREDICTION TABLE     
    sql_query = f"""
            INSERT INTO {update_prediction_table}
            SELECT
                {pdr_payouts_table_name}.ID as ID,
                {pdr_payouts_table_name}.stake as stake,
                {pdr_payouts_table_name}.payout as payout,
                {pdr_payouts_table_name}.predvalue as predvalue,
                GREATEST({pdr_payouts_table_name}.timestamp,
                    {pdr_truevals_table_name}.timestamp) as last_event_timestamp,
                {pdr_truevals_table_name}.truevalue as truevalue,
            FROM
                {pdr_truevals_table_name}
            LEFT JOIN {pdr_payouts_table_name}
                ON {pdr_truevals_table_name}.ID = (SPLIT_PART({pdr_payouts_table_name}.ID, '-', 1)
                    || '-' || SPLIT_PART({pdr_payouts_table_name}.ID, '-', 2))
            WHERE 
                ({pdr_payouts_table_name}.timestamp > {st_ms}
                AND {pdr_payouts_table_name}.timestamp <= {fin_ms})
                OR
                ({pdr_truevals_table_name}.timestamp > {st_ms}
                AND {pdr_truevals_table_name}.timestamp <= {fin_ms})
        """
    
    # EXECUTE THE SQL QUERY
    db.execute_sql(sql_query)
    
    # UPDATE THE BRONZE PREDICTIONS TABLE
    # UPDATE ONLY NON NULL VALUES (COALESCE FUNCTION)
    sql_update_query = f"""
            UPDATE {bronze_prediction_table}
            SET
                stake = COALESCE({update_prediction_table}.stake, stake),
                payout = COALESCE({update_prediction_table}.payout, payout),
                predvalue = COALESCE({update_prediction_table}.predvalue, predvalue),
                last_event_timestamp = COALESCE({update_prediction_table}.last_event_timestamp, last_event_timestamp),
                truevalue = COALESCE({update_prediction_table}.truevalue, truevalue)
            FROM {update_prediction_table}
            WHERE {bronze_prediction_table}.ID = {update_prediction_table}.ID
        """
    
    db.execute_sql(sql_update_query)
