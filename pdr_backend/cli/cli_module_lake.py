import logging

from enforce_typing import enforce_types

from pdr_backend.lake.lake_info import LakeInfo
from pdr_backend.lake.lake_validate import LakeValidate
from pdr_backend.cli.cli_arguments_lake import LAKE_SUBCOMMANDS, LakeArgParser
from pdr_backend.lake.persistent_data_store import PersistentDataStore
from pdr_backend.lake.table import drop_tables_from_st
from pdr_backend.ppss.ppss import PPSS

from pdr_backend.lake.etl import ETL
from pdr_backend.lake.gql_data_factory import GQLDataFactory

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
    ppss = PPSS(yaml_filename=args.PPSS_FILE, network=args.NETWORK)

    lake_info = LakeInfo(ppss)
    lake_info.run()


@enforce_types
def do_lake_validate(args):
    ppss = PPSS(yaml_filename=args.PPSS_FILE, network=args.NETWORK)

    lake_validate = LakeValidate(ppss)
    lake_validate.run()


@enforce_types
def do_lake_query(args):
    """
    @description
        Query the lake for a table or view
    """
    ppss = PPSS(yaml_filename=args.PPSS_FILE, network=args.NETWORK)

    pds = PersistentDataStore(ppss, read_only=True)
    try:
        df = pds.query_data(args.QUERY)
        print(df)
    except Exception as e:
        logger.error("Error querying lake: %s", e)
        print(e)


@enforce_types
def do_lake_raw(args, nested_args=None):
    """
    @description
        This updates the raw lake data
        1. All subgraph data will be fetched
        
        Please use nested_args to control lake_ss
        ie: st_timestr, fin_timestr, lake_dir
    """
    ppss = PPSS(
        yaml_filename=args.PPSS_FILE,
        network=args.NETWORK,
        nested_override_args=nested_args,
    )

    try:
        gql_data_factory = GQLDataFactory(ppss)
        gql_data_factory.get_gql_tables()
    except Exception as e:
        logger.error("Error updating raw lake data: %s", e)
        print(e)


@enforce_types
def do_lake_raw_drop(args):
    ppss = PPSS(
        yaml_filename=args.PPSS_FILE,
        network=args.NETWORK,
    )

    pds = PersistentDataStore(ppss, read_only=False)
    drop_tables_from_st(pds, "raw", args.ST)


@enforce_types
def do_lake_raw_update(args):
    print(f"TODO: start ms = {args.ST}, end ms = {args.END}, ppss = {args.PPSS_FILE}")


@enforce_types
def do_lake_etl(args, nested_args=None):
    """
    @description
        This runs all dependencies to build analytics
        All raw, clean, and aggregate data will be generated
        1. All subgraph data will be fetched
        2. All analytic data will be built
        3. Lake contains all required data
        4. Dashboards read from lake

        Please use nested_args to control lake_ss
        ie: st_timestr, fin_timestr, lake_dir
    """
    ppss = PPSS(
        yaml_filename=args.PPSS_FILE,
        network=args.NETWORK,
        nested_override_args=nested_args,
    )

    gql_data_factory = GQLDataFactory(ppss)
    etl = ETL(ppss, gql_data_factory)
    etl.do_etl()


@enforce_types
def do_lake_etl_drop(args):
    ppss = PPSS(
        yaml_filename=args.PPSS_FILE,
        network=args.NETWORK,
    )

    pds = PersistentDataStore(ppss, read_only=False)
    drop_tables_from_st(pds, "etl", args.ST)


@enforce_types
def do_lake_etl_update(args):
    print(f"TODO: start ms = {args.ST}, end ms = {args.END}, ppss = {args.PPSS_FILE}")

