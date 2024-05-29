import logging
from typing import List
from pdr_backend.util.time_types import UnixTimeMs
from pdr_backend.lake.table import NamedTable
from pdr_backend.lake.trueval import Trueval
from pdr_backend.lake.slot import Slot
from duckdb_data_store import DuckDBDataStore
from pdr_backend.lake.table import TableType
from pdr_backend.lake.prediction import Prediction
from pdr_backend.lake.lake_mapper import LakeMapper
from typing import Type
from enforce_typing import enforce_types

@enforce_types
def relation_updater(
    lake_path: str,
    st_ms: UnixTimeMs,
    fin_ms: UnixTimeMs,
    source_dataclass: Type[LakeMapper],
    target_dataclass: Type[LakeMapper],
    where_clause: str
):
    """
    Update the target table with the latest data from the source table.
    @args:
    lake_path: str: Path to the lake directory.
    st_ms: UnixTimeMs: Start time in milliseconds.
    fin_ms: UnixTimeMs: End time in milliseconds.
    source_dataclass: Type[LakeMapper]: The source dataclass.
    target_dataclass: Type[LakeMapper]: The target dataclass.
    where_clause: str: The where clause to filter the data. it should include the source and target aliases.
    """
    
    
    logger = logging.getLogger("lake")

    source_table = NamedTable.from_dataclass(source_dataclass)
    target_table = NamedTable.from_dataclass(target_dataclass, TableType.COPY)

    logger.info(f"Updating COPY {target_table.name} table with {source_table.name} data...")

    DuckDBDataStore(lake_path).execute_sql(
        f"""
            UPDATE {target_table.fullname} AS target
            SET truevalue = source.truevalue
            FROM {source_table.fullname} AS source
            WHERE {where_clause.format(source=source_table.alias, target=target_table.alias)}
            AND source.timestamp >= {st_ms}
            AND source.timestamp <= {fin_ms}
        """
    )

    logger.info(f"Updated {target_table.name} table with {source_table.name} data.")

@enforce_types
def on_trueval_update_slot(
    lake_path: str,
    st_ms: UnixTimeMs,
    fin_ms: UnixTimeMs
):
    """
    Update the Raw Slot table with the latest TrueVal data.
    """
    relation_updater(
        lake_path,
        st_ms,
        fin_ms,
        Trueval,
        Slot,
        "{source}.ID = {target}.ID"
    )

@enforce_types
def on_trueval_update_prediction(
    lake_path: str,
    st_ms: UnixTimeMs,
    fin_ms: UnixTimeMs
):
    """
    Update the Raw Prediction table with the latest TrueVal data.
    """
    relation_updater(
        lake_path,
        st_ms,
        fin_ms,
        Trueval,
        Prediction,
        """{target}.ID = (
            SPLIT_PART({source}.ID, '-', 1) || '-' || SPLIT_PART({source}.ID, '-', 2)"""
    )