import logging
import sys
from argparse import Namespace

from enforce_typing import enforce_types

from pdr_backend.cli.nested_arg_parser import NestedArgParser

logger = logging.getLogger("cli")

HELP_TOP = """Predictoor tool

Usage: pdr sim|..
"""

HELP_MAIN = """
Main tools:
  pdr sim PPSS_FILE
"""

HELP_HELP = """
Detailed help:
  pdr <cmd> -h
  pdr help_long
"""

HELP_SIGN = """
Transactions are signed with envvar 'PRIVATE_KEY`.
"""

HELP_OTHER_TOOLS = """
Power tools:
  pdr ohlcv PPSS_FILE 

Dev tools:
  pytest, black, mypy, pylint, ..
"""

HELP_SHORT = HELP_TOP + HELP_MAIN + HELP_HELP + HELP_SIGN

HELP_LONG = HELP_TOP + HELP_MAIN + HELP_HELP + HELP_OTHER_TOOLS + HELP_SIGN


# ========================================================================
# mixins
@enforce_types
class APPROACH_Mixin:
    def add_argument_APPROACH(self):
        self.add_argument("APPROACH", type=int, help="1|2|..")


@enforce_types
class PPSS_Mixin:
    def add_argument_PPSS(self):
        self.add_argument("PPSS_FILE", type=str, help="PPSS yaml settings file")


# ========================================================================
# argparser base classes
class CustomArgParser(NestedArgParser):
    def add_arguments_bulk(self, command_name, arguments):
        self.add_argument("command", choices=[command_name])

        for arg in arguments:
            func = getattr(self, f"add_argument_{arg}")
            func()


@enforce_types
class _ArgParser_PPSS(CustomArgParser, PPSS_Mixin):
    @enforce_types
    def __init__(self, description: str, command_name: str):
        super().__init__(description=description)
        self.add_arguments_bulk(command_name, ["PPSS"])


@enforce_types
# pylint: disable=too-many-ancestors
class _ArgParser_APPROACH_PPSS(
    CustomArgParser,
    APPROACH_Mixin,
    PPSS_Mixin,
):
    def __init__(self, description: str, command_name: str):
        super().__init__(description=description)
        self.add_arguments_bulk(command_name, ["APPROACH", "PPSS"])


# ========================================================================
# actual arg-parser implementations are just aliases to argparser base classes
# In order of help text.


@enforce_types
def do_help_short(status_code=0):
    print(HELP_SHORT)
    sys.exit(status_code)


@enforce_types
def do_help_long(status_code=0):
    print(HELP_LONG)
    sys.exit(status_code)


@enforce_types
def print_args(arguments: Namespace, nested_args: dict):
    arguments_dict = arguments.__dict__
    command = arguments_dict.pop("command", None)

    logger.info("pdr %s: Begin", command)
    logger.info("Arguments:")

    for arg_k, arg_v in arguments_dict.items():
        logger.info("%s=%s", arg_k, arg_v)

    logger.info("Nested args: %s", nested_args)


## below, list *ArgParser classes in same order as HELP_LONG

# tools list
SimArgParser = _ArgParser_PPSS
OHLCVArgParser = _ArgParser_PPSS


# below, list each entry in defined_parsers in same order as HELP_LONG
defined_parsers = {
    "do_sim": SimArgParser("Run simulation", "sim"),
    "do_ohlcv": OHLCVArgParser("Run the ohlcv tool", "ohlcv"),
}


def get_arg_parser(func_name):
    if func_name not in defined_parsers:
        raise ValueError(f"Unknown function name: {func_name}")

    return defined_parsers[func_name]
