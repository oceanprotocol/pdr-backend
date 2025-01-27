import logging
import sys

from enforce_typing import enforce_types

from pdr_backend.cli.cli_arguments import (
    do_help_long,
    do_help_short,
    get_arg_parser,
    print_args,
)
from pdr_backend.lake.ohlcv_data_factory import OhlcvDataFactory
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.sim.sim_engine import SimEngine

logger = logging.getLogger("cli")


@enforce_types
def _do_main():
    if len(sys.argv) <= 1 or sys.argv[1] == "help":
        do_help_short(0)
    if sys.argv[1] == "help_long":
        do_help_long(0)

    func_name = f"do_{sys.argv[1]}"
    func = globals().get(func_name)
    if func is None:
        do_help_long(1)

    parser = get_arg_parser(func_name)
    args, nested_args = parser.parse_known_args()

    print_args(args, nested_args)

    func(args, nested_args)


# ========================================================================
# actual cli implementations. Given in same order as HELP_LONG


# do_help() is implemented in cli_arguments and imported, so nothing needed here


@enforce_types
def do_sim(args, nested_args=None):
    ppss = PPSS(
        yaml_filename=args.PPSS_FILE,
        nested_override_args=nested_args,
    )
    feedset = ppss.predictoor_ss.predict_train_feedsets[0]
    if len(ppss.predictoor_ss.predict_train_feedsets) > 0:
        logger.warning("Multiple predict feeds provided, using the first one")
    sim_engine = SimEngine(ppss, feedset)
    sim_engine.run()


@enforce_types
# pylint: disable=unused-argument
def do_ohlcv(args, nested_args=None):
    ppss = args.PPSS
    ohlcv_data_factory = OhlcvDataFactory(ppss.lake_ss)
    df = ohlcv_data_factory.get_mergedohlcv_df()
    print(df)

