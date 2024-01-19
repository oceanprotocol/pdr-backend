import sys
from argparse import ArgumentParser as ArgParser
from argparse import Namespace

from enforce_typing import enforce_types

HELP_LONG = """Predictoor tool

Usage: pdr xpmt|predictoor|trader|..

Main tools:
  pdr xpmt PPSS_FILE
  pdr predictoor APPROACH PPSS_FILE NETWORK
  pdr trader APPROACH PPSS_FILE NETWORK
  pdr lake PPSS_FILE NETWORK
  pdr claim_OCEAN PPSS_FILE
  pdr claim_ROSE PPSS_FILE

Utilities:
  pdr help
  pdr <cmd> -h
  pdr get_predictoors_info ST END PQDIR PPSS_FILE NETWORK --PDRS
  pdr get_predictions_info ST END PQDIR PPSS_FILE NETWORK --FEEDS
  pdr get_traction_info ST END PQDIR PPSS_FILE NETWORK --FEEDS
  pdr check_network PPSS_FILE NETWORK --LOOKBACK_HOURS

Transactions are signed with envvar 'PRIVATE_KEY`.

Tools for core team:
  pdr trueval PPSS_FILE NETWORK
  pdr dfbuyer PPSS_FILE NETWORK
  pdr publisher PPSS_FILE NETWORK
  pdr topup PPSS_FILE NETWORK
  pytest, black, mypy, pylint, ..
"""


# ========================================================================
# mixins
@enforce_types
class APPROACH_Mixin:
    def add_argument_APPROACH(self):
        self.add_argument("APPROACH", type=int, help="1|2|..")


@enforce_types
class ST_Mixin:
    def add_argument_ST(self):
        self.add_argument("ST", type=str, help="Start date yyyy-mm-dd")


@enforce_types
class END_Mixin:
    def add_argument_END(self):
        self.add_argument("END", type=str, help="End date yyyy-mm-dd")


@enforce_types
class PQDIR_Mixin:
    def add_argument_PQDIR(self):
        self.add_argument("PQDIR", type=str, help="Parquet output dir")


@enforce_types
class PPSS_Mixin:
    def add_argument_PPSS(self):
        self.add_argument("PPSS_FILE", type=str, help="PPSS yaml settings file")


@enforce_types
class NETWORK_Mixin:
    def add_argument_NETWORK(self):
        self.add_argument(
            "NETWORK",
            type=str,
            help="sapphire-testnet|sapphire-mainnet|development|barge-pytest|..",
        )


@enforce_types
class PDRS_Mixin:
    def add_argument_PDRS(self):
        self.add_argument(
            "--PDRS",
            type=str,
            help="Predictoor address(es), separated by comma. If not specified, uses all.",
            required=False,
        )


@enforce_types
class FEEDS_Mixin:
    def add_argument_FEEDS(self):
        self.add_argument(
            "--FEEDS",
            type=str,
            default="",
            help="Predictoor feed address(es). If not specified, uses all.",
            required=False,
        )


@enforce_types
class LOOKBACK_Mixin:
    def add_argument_LOOKBACK(self):
        self.add_argument(
            "--LOOKBACK_HOURS",
            default=24,
            type=int,
            help="# hours to check back on",
            required=False,
        )


# ========================================================================
# argparser base classes
class CustomArgParser(ArgParser):
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
class _ArgParser_PPSS_NETWORK(CustomArgParser, PPSS_Mixin, NETWORK_Mixin):
    @enforce_types
    def __init__(self, description: str, command_name: str):
        super().__init__(description=description)
        self.add_arguments_bulk(command_name, ["PPSS", "NETWORK"])


@enforce_types
class _ArgParser_APPROACH_PPSS_NETWORK(
    CustomArgParser,
    APPROACH_Mixin,
    PPSS_Mixin,
    NETWORK_Mixin,
):
    def __init__(self, description: str, command_name: str):
        super().__init__(description=description)
        self.add_arguments_bulk(command_name, ["APPROACH", "PPSS", "NETWORK"])


@enforce_types
class _ArgParser_PPSS_NETWORK_LOOKBACK(
    CustomArgParser,
    PPSS_Mixin,
    NETWORK_Mixin,
    LOOKBACK_Mixin,
):
    @enforce_types
    def __init__(self, description: str, command_name: str):
        super().__init__(description=description)
        self.add_arguments_bulk(command_name, ["PPSS", "NETWORK", "LOOKBACK"])


@enforce_types
class _ArgParser_ST_END_PQDIR_NETWORK_PPSS_PDRS(
    CustomArgParser,
    ST_Mixin,
    END_Mixin,
    PQDIR_Mixin,
    PPSS_Mixin,
    NETWORK_Mixin,
    PDRS_Mixin,
):  # pylint: disable=too-many-ancestors
    @enforce_types
    def __init__(self, description: str, command_name: str):
        super().__init__(description=description)
        self.add_arguments_bulk(
            command_name, ["ST", "END", "PQDIR", "PPSS", "NETWORK", "PDRS"]
        )


@enforce_types
class _ArgParser_ST_END_PQDIR_NETWORK_PPSS_FEEDS(
    CustomArgParser,
    ST_Mixin,
    END_Mixin,
    PQDIR_Mixin,
    PPSS_Mixin,
    NETWORK_Mixin,
    FEEDS_Mixin,
):  # pylint: disable=too-many-ancestors
    @enforce_types
    def __init__(self, description: str, command_name: str):
        super().__init__(description=description)
        self.add_arguments_bulk(
            command_name, ["ST", "END", "PQDIR", "PPSS", "NETWORK", "FEEDS"]
        )


# ========================================================================
# actual arg-parser implementations are just aliases to argparser base classes
# In order of help text.


@enforce_types
def do_help_long(status_code=0):
    print(HELP_LONG)
    sys.exit(status_code)


@enforce_types
def print_args(arguments: Namespace):
    arguments_dict = arguments.__dict__
    command = arguments_dict.pop("command", None)

    print(f"pdr {command}: Begin")
    print("Arguments:")

    for arg_k, arg_v in arguments_dict.items():
        print(f"{arg_k}={arg_v}")


XpmtArgParser = _ArgParser_PPSS

PredictoorArgParser = _ArgParser_APPROACH_PPSS_NETWORK

TraderArgParser = _ArgParser_APPROACH_PPSS_NETWORK

LakeArgParser = _ArgParser_PPSS_NETWORK

ClaimOceanArgParser = _ArgParser_PPSS

ClaimRoseArgParser = _ArgParser_PPSS

GetPredictoorsInfoArgParser = _ArgParser_ST_END_PQDIR_NETWORK_PPSS_PDRS

GetPredictionsInfoArgParser = _ArgParser_ST_END_PQDIR_NETWORK_PPSS_FEEDS

GetTractionInfoArgParser = _ArgParser_ST_END_PQDIR_NETWORK_PPSS_FEEDS

CheckNetworkArgParser = _ArgParser_PPSS_NETWORK_LOOKBACK

TruevalArgParser = _ArgParser_PPSS_NETWORK

DfbuyerArgParser = _ArgParser_PPSS_NETWORK

PublisherArgParser = _ArgParser_PPSS_NETWORK

TopupArgParser = _ArgParser_PPSS_NETWORK

defined_parsers = {
    "do_xpmt": XpmtArgParser("Run experiment / simulation", "xpmt"),
    "do_predictoor": PredictoorArgParser("Run a predictoor bot", "predictoor"),
    "do_trader": TraderArgParser("Run a trader bot", "trader"),
    "do_lake": LakeArgParser("Run the lake tool", "lake"),
    "do_claim_OCEAN": ClaimOceanArgParser("Claim OCEAN", "claim_OCEAN"),
    "do_claim_ROSE": ClaimRoseArgParser("Claim ROSE", "claim_ROSE"),
    "do_get_predictoors_info": GetPredictoorsInfoArgParser(
        "For specified predictoors, report {accuracy, ..} of each predictoor",
        "get_predictoors_info",
    ),
    "do_get_predictions_info": GetPredictionsInfoArgParser(
        "For specified feeds, report {accuracy, ..} of each predictoor",
        "get_predictions_info",
    ),
    "do_get_traction_info": GetTractionInfoArgParser(
        "Get traction info: # predictoors vs time, etc",
        "get_traction_info",
    ),
    "do_check_network": CheckNetworkArgParser("Check network", "check_network"),
    "do_trueval": TruevalArgParser("Run trueval bot", "trueval"),
    "do_dfbuyer": DfbuyerArgParser("Run dfbuyer bot", "dfbuyer"),
    "do_publisher": PublisherArgParser("Publish feeds", "publisher"),
    "do_topup": TopupArgParser("Topup OCEAN and ROSE in dfbuyer, trueval, ..", "topup"),
}


def get_arg_parser(func_name):
    if func_name not in defined_parsers:
        raise ValueError(f"Unknown function name: {func_name}")

    return defined_parsers[func_name]
