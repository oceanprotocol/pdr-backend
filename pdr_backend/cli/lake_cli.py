import logging
import os
from argparse import ArgumentParser

from enforce_typing import enforce_types

from pdr_backend.analytics.lakeinfo import LakeInfo
from pdr_backend.lake.persistent_data_store import PersistentDataStore

logger = logging.getLogger("cli")
LAKE_SUBCOMMANDS = ["describe", "query"]


def do_lake_subcommand(args):
    assert args[0] in LAKE_SUBCOMMANDS, f"Invalid lake subcommand: {args[0]}"

    parser = ArgumentParser()
    parser.add_argument("subcommand", type=str, help="")
    parser.add_argument("LAKE_DIR", type=str, help="The directory of the lake")

    if args[0] == "query":
        parser.add_argument("QUERY", type=str, help="The query to run")

    args = parser.parse_args(args)
    lake_dir = get_lake_dir(args.LAKE_DIR)

    func_name = f"do_lake_{args.subcommand}"
    func = globals().get(func_name)
    func(lake_dir, args)


def get_lake_dir(s):
    if s != os.path.abspath(s):  # rel path given; needs an abs path
        return os.path.abspath(s)
    # abs path given
    return s


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
