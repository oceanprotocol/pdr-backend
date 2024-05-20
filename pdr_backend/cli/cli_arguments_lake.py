import logging
import os
from argparse import ArgumentParser
from typing import Union

from enforce_typing import enforce_types

from pdr_backend.cli.cli_arguments import NETWORK_Mixin, PPSS_Mixin
from pdr_backend.util.time_types import UnixTimeMs

logger = logging.getLogger("cli")
LAKE_SUBCOMMANDS = ["describe", "validate", "query", "raw", "etl"]
SUPPORTS_L2_COMMANDS = ["raw", "etl"]


# utilities
@enforce_types
def timestr(s: str, allows_now=False) -> UnixTimeMs:
    if s == "now" and not allows_now:
        raise TypeError

    try:
        return UnixTimeMs.from_timestr(s)
    except ValueError as exc:
        extra_msg = " or 'now'" if allows_now else ""
        raise TypeError(
            f"Invalid timestr value {s}. Please use the format 'yyyy-mm-dd'{extra_msg}."
        ) from exc


@enforce_types
def timestr_or_now(s: str) -> Union[UnixTimeMs, str]:
    if s == "now":
        return "now"

    return timestr(s)


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

        self.add_argument_PPSS()
        self.add_argument_NETWORK()

        if plain_args[0] == "query":
            self.add_argument("QUERY", type=str, help="The query to run")
        elif plain_args[1] == "drop":
            self.add_argument("ST", type=timestr, help="Start date yyyy-mm-dd")

        if plain_args[0] == "describe":
            self.add_argument(
                "--HTML",
                action="store_true",
                default=False,
                help="If --HTML then run describe in HTML app",
                required=False,
            )
