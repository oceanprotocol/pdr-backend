import logging

from enforce_typing import enforce_types

from pdr_backend.analytics.lakeinfo import LakeInfo
from pdr_backend.cli.cli_arguments_lake import LAKE_SUBCOMMANDS, LakeArgParser
from pdr_backend.lake.persistent_data_store import PersistentDataStore
from pdr_backend.lake.table import drop_tables_from_st

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
    func(parsed_args)


# subcommands
@enforce_types
def do_lake_describe(args):
    lake_info = LakeInfo(args.LAKE_DIR)
    lake_info.run()


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
def do_lake_raw_drop(args):
    pds = PersistentDataStore(args.LAKE_DIR, read_only=False)
    drop_tables_from_st(pds, "raw", args.ST)


@enforce_types
def do_lake_raw_update(args):
    print(f"TODO: start ms = {args.ST}, end ms = {args.END}, ppss = {args.PPSS_FILE}")


@enforce_types
def do_lake_etl_drop(args):
    pds = PersistentDataStore(args.LAKE_DIR, read_only=False)
    drop_tables_from_st(pds, "etl", args.ST)


@enforce_types
def do_lake_etl_update(args):
    print(f"TODO: start ms = {args.ST}, end ms = {args.END}, ppss = {args.PPSS_FILE}")
