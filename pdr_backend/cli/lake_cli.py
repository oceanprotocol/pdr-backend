import logging
import os
from argparse import ArgumentParser

from enforce_typing import enforce_types

from pdr_backend.analytics.lakeinfo import LakeInfo
from pdr_backend.cli.cli_arguments import PPSS_Mixin, NETWORK_Mixin
from pdr_backend.lake.persistent_data_store import PersistentDataStore
from pdr_backend.util.time_types import UnixTimeMs

logger = logging.getLogger("cli")
LAKE_SUBCOMMANDS = ["describe", "query", "raw", "etl"]
SUPPORTS_L2_COMMANDS = ["raw", "etl"]


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


@enforce_types
class LakeArgParser(ArgumentParser, PPSS_Mixin, NETWORK_Mixin):
    def __init__(self, plain_args):
        super().__init__()
        self.add_argument("subcommand", type=str, help="")

        if plain_args[0] in SUPPORTS_L2_COMMANDS:
            self.add_argument(
                "l2_subcommand_type",
                type=str,
                choices=["drop", "update"],
                help="drop or update",
            )

        if plain_args[0] in SUPPORTS_L2_COMMANDS and plain_args[1] == "update":
            self.add_argument_PPSS()
            self.add_argument_NETWORK()
        else:
            self.add_argument(
                "LAKE_DIR", type=str_as_abspath, help="The directory of the lake"
            )

        if plain_args[0] == "query":
            self.add_argument("QUERY", type=str, help="The query to run")
        elif plain_args[0] in SUPPORTS_L2_COMMANDS:
            self.add_argument("ST", type=timestr, help="Start date yyyy-mm-dd")
            if plain_args[1] == "update":
                self.add_argument("END", type=timestr, help="End date yyyy-mm-dd")


# entrypoint
def do_lake_subcommand(args):
    assert args[0] in LAKE_SUBCOMMANDS, f"Invalid lake subcommand: {args[0]}"

    parser = LakeArgParser(args)
    parsed_args = parser.parse_args(args)

    func_name = f"do_lake_{parsed_args.subcommand}"
    func = globals().get(func_name)
    func(parsed_args)


@enforce_types
# pylint: disable=unused-argument
def do_lake_describe(args):
    lake_info = LakeInfo(args.LAKE_DIR)
    lake_info.run()


def remove_prefix(table_name: str) -> str:
    table_name = table_name.removeprefix("_")
    table_name = table_name.removeprefix("temp_")
    table_name = table_name.removeprefix("_")
    table_name = table_name.removeprefix("etl_")
    table_name = table_name.removeprefix("temp_")

    return table_name


def is_etl_table(table_name: str) -> bool:
    table_name = remove_prefix(table_name)
    return (
        table_name.startswith("bronze_")
        or table_name.startswith("silver_")
        or table_name.startswith("gold_")
    )


def drop_tables_from_st(pds: PersistentDataStore, type_filter: str, st):
    trunc_count = table_count = 0
    if type_filter not in ["raw", "etl"]:
        return

    table_names = pds.get_table_names()

    for table_name in table_names:
        if type_filter == "etl" and not is_etl_table(table_name):
            logger.info("skipping non-etl table %s", table_name)
            continue

        if type_filter == "raw" and is_etl_table(table_name):
            logger.info("skipping etl table %s", table_name)
            continue

        logger.info("drop table %s starting at %s", table_name, st)
        rows_before = pds.row_count(table_name)
        logger.info("rows before: %s", rows_before)
        pds.query_data(f"DELETE FROM {table_name} WHERE timestamp >= {st}")
        rows_after = pds.row_count(table_name)
        logger.info("rows after: %s", rows_after)
        if rows_before != rows_after:
            table_count += 1
            trunc_count += rows_before - rows_after

    logger.info("truncated %s rows from %s tables", trunc_count, table_count)


@enforce_types
def do_lake_query(args):
    """
    @description
        Query the lake for a table or view
    """
    pds = PersistentDataStore(args.LAKE_DIR, read_only=True)
    try:
        df = pds.query_data(args.QUERY)
        print(df)
    except Exception as e:
        logger.error("Error querying lake: %s", e)
        print(e)


@enforce_types
def do_lake_raw(args):
    """
    @description
        Drop or update raw data
    """
    if args.l2_subcommand_type == "drop":
        do_raw_drop(args)
    elif args.l2_subcommand_type == "update":
        do_raw_update(args)


@enforce_types
def do_raw_drop(args):
    pds = PersistentDataStore(args.LAKE_DIR, read_only=False)
    drop_tables_from_st(pds, "raw", args.ST)


@enforce_types
def do_raw_update(args):
    print(f"TODO: start ms = {args.ST}, end ms = {args.END}, ppss = {args.PPSS_FILE}")


@enforce_types
def do_lake_etl(args):
    if args.l2_subcommand_type == "drop":
        do_etl_drop(args)
    elif args.l2_subcommand_type == "update":
        do_etl_update(args)


@enforce_types
def do_etl_drop(args):
    pds = PersistentDataStore(args.LAKE_DIR, read_only=False)
    drop_tables_from_st(pds, "etl", args.ST)


@enforce_types
def do_etl_update(args):
    print(f"TODO: start ms = {args.ST}, end ms = {args.END}, ppss = {args.PPSS_FILE}")
