#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
import os

from enforce_typing import enforce_types

from pdr_backend.cli.cli_arguments_lake import LAKE_SUBCOMMANDS, LakeArgParser
from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.lake.etl import ETL
from pdr_backend.lake.gql_data_factory import GQLDataFactory
from pdr_backend.lake.table import drop_tables_from_st
from pdr_backend.lake_info.lake_info import LakeInfo
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.util.time_types import UnixTimeMs
from pdr_backend.util.networkutil import download_file
from pdr_backend.util.csvs import export_table_data_to_parquet_files

logger = logging.getLogger("cli")


# entrypoint
def do_lake_subcommand(args):
    assert args[0] in LAKE_SUBCOMMANDS, f"Invalid lake subcommand: {args[0]}"

    parser = LakeArgParser(args)
    parsed_args = parser.parse_args(args)

    func_name = f"do_lake_{parsed_args.subcommand}"

    if hasattr(parsed_args, "l2_subcommand_type"):
        func_name += f"_{parsed_args.l2_subcommand_type}"

    func = globals().get(func_name)

    ppss = PPSS(yaml_filename=parsed_args.PPSS_FILE, network=parsed_args.NETWORK)

    # Every lake interaction goes through here and we don't have any processes/looping yet
    # So, we can resolve the st_timestr and fin_timestr here
    # Let's transform "1d ago" or "now" into a UnixTimeMs object
    st_ts_ms = UnixTimeMs.from_timestr(ppss.lake_ss.st_timestr)
    fin_ts_ms = UnixTimeMs.from_timestr(ppss.lake_ss.fin_timestr)

    # And then let's update the ppss object with these new values
    # So we don't have any time drifting while we're running the lake commands
    ppss.lake_ss.d["st_timestr"] = st_ts_ms.to_timestr()
    ppss.lake_ss.d["fin_timestr"] = fin_ts_ms.to_timestr()

    # Finally, pass fixed st_timestr and fin_timestr throuh ppss
    func(parsed_args, ppss)


# subcommands
@enforce_types
def do_lake_raw_update(_, ppss):
    """
    @description
        This updates the raw lake data
        1. All subgraph data will be fetched

        Please use nested_args to control lake_ss
        ie: st_timestr, fin_timestr, lake_dir
    """
    try:
        gql_data_factory = GQLDataFactory(ppss)
        gql_data_factory._update()
    except Exception as e:
        logger.error("Error updating raw lake data: %s", e)
        print(e)


@enforce_types
def do_lake_etl_update(_, ppss):
    """
        @description
            This runs all dependencies to build analytics
            All raw, clean, and aggregate data will be generated
            1. All subgraph data will be fetched
            2. All analytic data will be built
            3. Lake contains all required data
            4. Dashboards read from lake
    #
            Please use nested_args to control lake_ss
            ie: st_timestr, fin_timestr, lake_dir
    """
    gql_data_factory = GQLDataFactory(ppss)
    etl = ETL(ppss, gql_data_factory)
    etl.do_etl()


@enforce_types
def do_lake_raw_drop(args, ppss):
    db = DuckDBDataStore(ppss.lake_ss.lake_dir, read_only=False)
    drop_tables_from_st(db, "raw", args.ST)


@enforce_types
def do_lake_etl_drop(args, ppss):
    db = DuckDBDataStore(ppss.lake_ss.lake_dir, read_only=False)
    drop_tables_from_st(db, "etl", args.ST)


@enforce_types
def do_lake_describe(args, ppss):
    lake_info = LakeInfo(ppss, use_html=args.HTML)
    lake_info.run()


@enforce_types
def do_lake_validate(_, ppss):
    lake_info = LakeInfo(ppss)
    lake_info.run_validation()


@enforce_types
def do_lake_query(args, ppss):
    """
    @description
        Query the lake for a table or view
    """
    db = DuckDBDataStore(ppss.lake_ss.lake_dir, read_only=True)
    try:
        df = db.query_data(args.QUERY)
        print(df)
        print("Rows:", len(df))
    except Exception as e:
        logger.error("Error querying lake: %s", e)
        print(e)


def do_lake_setupdata(args, ppss):
    """
    Downloads the DuckDB file from the pdr-lake-cache repository
    and places it into the lake_folder.
    """
    lake_folder = ppss.lake_ss.lake_dir
    duckdb_url = "https://raw.githubusercontent.com/oceanprotocol/pdr-lake-cache/main/exports/duckdb_backup.db"

    if not os.path.exists(lake_folder):
        os.makedirs(lake_folder)

    file_path = os.path.join(lake_folder, "duckdb.db")

    try:
        logger.info("Downloading DuckDB from %s", duckdb_url)
        download_file(duckdb_url, file_path)
        logger.info("DuckDB successfully downloaded to %s", file_path)
        export_table_data_to_parquet_files(ppss)
    except Exception as e:
        logger.error("Failed to download the DuckDB file: %s", str(e))
