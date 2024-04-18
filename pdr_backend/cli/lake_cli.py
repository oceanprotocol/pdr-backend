import logging
import os
from argparse import ArgumentParser

from enforce_typing import enforce_types

from pdr_backend.analytics.lakeinfo import LakeInfo
from pdr_backend.lake.persistent_data_store import PersistentDataStore
from pdr_backend.util.time_types import UnixTimeMs

logger = logging.getLogger("cli")
LAKE_SUBCOMMANDS = ["describe", "query", "raw", "etl"]


# utilities
@enforce_types
def timestr(s: str) -> UnixTimeMs:
    try:
        return UnixTimeMs.from_timestr(s)
    except ValueError as exc:
        raise TypeError(
            f"Invalid timestr value {s}. Please use the format 'yyyy-mm-dd'."
        ) from exc


@enforce_types
def str_as_abspath(s: str):
    if s != os.path.abspath(s):  # rel path given; needs an abs path
        return os.path.abspath(s)
    # abs path given
    return s


# entrypoint
def do_lake_subcommand(args):
    assert args[0] in LAKE_SUBCOMMANDS, f"Invalid lake subcommand: {args[0]}"

    parser = ArgumentParser()
    parser.add_argument("subcommand", type=str, help="")

    if args[0] in ["raw", "etl"]:
        parser.add_argument(
            "raw_subcommand_type",
            type=str,
            choices=["drop", "update"],
            help="drop or update",
        )

    parser.add_argument(
        "LAKE_DIR", type=str_as_abspath, help="The directory of the lake"
    )

    if args[0] == "query":
        parser.add_argument("QUERY", type=str, help="The query to run")
    elif args[0] in ["raw", "etl"]:
        parser.add_argument("ST", type=timestr, help="Start date yyyy-mm-dd")
        if args[1] == "update":
            parser.add_argument("END", type=timestr, help="End date yyyy-mm-dd")

    args = parser.parse_args(args)

    func_name = f"do_lake_{args.subcommand}"
    func = globals().get(func_name)
    func(args.LAKE_DIR, args)


@enforce_types
# pylint: disable=unused-argument
def do_lake_describe(lake_dir: str, args):
    lake_info = LakeInfo(lake_dir)
    lake_info.run()


@enforce_types
def do_lake_query(lake_dir: str, args):
    """
    @description
        Query the lake for a table or view
    """
    pds = PersistentDataStore(lake_dir, read_only=True)
    try:
        df = pds.query_data(args.QUERY)
        print(df)
    except Exception as e:
        logger.error("Error querying lake: %s", e)
        print(e)


@enforce_types
def do_lake_raw(lake_dir: str, args):
    """
    @description
        Drop or update raw data
    """
    pds = PersistentDataStore(lake_dir, read_only=False)
    if args.raw_subcommand_type == "drop":
        do_raw_drop(pds, args)
    elif args.raw_subcommand_type == "update":
        do_raw_update(pds, args)


@enforce_types
def do_raw_drop(pds: PersistentDataStore, args):
    assert pds  # silence unused warning until we use it
    print(f"TODO: start ms = {args.ST}")


@enforce_types
def do_raw_update(pds: PersistentDataStore, args):
    assert pds  # silence unused warning until we use it
    print(f"TODO: start ms = {args.ST}, end ms = {args.END}")


@enforce_types
def do_lake_etl(lake_dir: str, args):
    pds = PersistentDataStore(lake_dir, read_only=False)
    if args.raw_subcommand_type == "drop":
        do_etl_drop(pds, args)
    elif args.raw_subcommand_type == "update":
        do_etl_update(pds, args)


@enforce_types
def do_etl_drop(pds: PersistentDataStore, args):
    trunc_count = table_count = 0

    for table_name in pds.get_table_names():
        logger.info("drop table %s starting at %s", table_name, args.ST)
        rows_before = pds.row_count(table_name)
        logger.info("rows before: %s", rows_before)
        pds.query_data(f"DELETE FROM {table_name} WHERE timestamp >= {args.ST}")
        rows_after = pds.row_count(table_name)
        logger.info("rows after: %s", rows_after)
        if rows_before != rows_after:
            table_count += 1
            trunc_count += rows_before - rows_after

    logger.info("truncated %s rows from %s tables", trunc_count, table_count)


@enforce_types
def do_etl_update(pds: PersistentDataStore, args):
    assert pds  # silence unused warning until we use it
    print(f"TODO: start ms = {args.ST}, end ms = {args.END}")
