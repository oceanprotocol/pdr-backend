from argparse import ArgumentParser as ArgParser
from argparse import Namespace
import sys

from enforce_typing import enforce_types

HELP_LONG = """Predictoor tool

Usage: pdr sim|predictoor|trader|..

Main tools:
  pdr sim YAML_FILE
  pdr predictoor APPROACH YAML_FILE NETWORK
  pdr trader APPROACH YAML_FILE NETWORK
  pdr claim_OCEAN YAML_FILE
  prd claim_ROSE YAML_FILE

Utilities:
  pdr help
  pdr <cmd> -h
  pdr get_predictoor_info PDR_ADDR1[,ADDR2,..] ST END CSVDIR YAML_FILE NETWORK
  pdr check_network YAML_FILE NETWORK --LOOKBACK_HOURS

Transactions are signed with envvar 'PRIVATE_KEY`.

Tools for core team:
  pdr trueval YAML_FILE NETWORK
  pdr dfbuyer YAML_FILE NETWORK
  pdr publisher YAML_FILE NETWORK
  pdr topup YAML_FILE NETWORK
  pytest, black, mypy, pylint, ..
"""


# ========================================================================
# utilities


@enforce_types
def print_args(arguments: Namespace):
    arguments_dict = arguments.__dict__
    command = arguments_dict.pop("command", None)

    print(f"dftool {command}: Begin")
    print("Arguments:")

    for arg_k, arg_v in arguments_dict.items():
        print(f"{arg_k}={arg_v}")


@enforce_types
class YAML_Mixin:
    def add_argument_YAML(self):
        self.add_argument("YAML_FILE", type=str, help="PPSS settings file")


@enforce_types
class APPROACH_Mixin:
    def add_argument_APPROACH(self):
        self.add_argument("APPROACH", type=int, help="1|2|..")


@enforce_types
class CSVDIR_Mixin:
    def add_argument_CSVDIR(self):
        self.add_argument("CSVDIR", type=str, help="Csv output dir")


@enforce_types
class NETWORK_Mixin:
    def add_argument_NETWORK(self):
        self.add_argument(
            "NETWORK",
            type=str,
            help="sapphire-testnet|sapphire-mainnet|barge-pdr|barge-pytest",
        )


@enforce_types
class _ArgParser_YAML(ArgParser, YAML_Mixin):
    @enforce_types
    def __init__(self, description: str, command_name: str):
        super().__init__(description=description)
        self.add_argument("command", choices=[command_name])
        self.add_argument_YAML()


@enforce_types
class _ArgParser_YAML_NETWORK(ArgParser, NETWORK_Mixin, YAML_Mixin):
    @enforce_types
    def __init__(self, description: str, command_name: str):
        super().__init__(description=description)
        self.add_argument("command", choices=[command_name])
        self.add_argument_YAML()
        self.add_argument_NETWORK()


@enforce_types
class _ArgParser_APPROACH_YAML_NETWORK(
    ArgParser,
    APPROACH_Mixin,
    NETWORK_Mixin,
    YAML_Mixin,
):
    def __init__(self, description: str, command_name: str):
        super().__init__(description=description)
        self.add_argument("command", choices=[command_name])
        self.add_argument_APPROACH()
        self.add_argument_YAML()
        self.add_argument_NETWORK()


# ========================================================================
# actual arg-parser implementations. In order of help text.


@enforce_types
class SimArgParser(ArgParser, YAML_Mixin):
    def __init__(self, description: str, command_name: str):
        super().__init__(description=description)
        self.add_argument("command", choices=[command_name])
        self.add_argument_YAML()


PredictoorArgParser = _ArgParser_APPROACH_YAML_NETWORK

TraderArgParser = _ArgParser_APPROACH_YAML_NETWORK

ClaimOceanArgParser = _ArgParser_YAML

ClaimRoseArgParser = _ArgParser_YAML


@enforce_types
def do_help_long(status_code=0):
    print(HELP_LONG)
    sys.exit(status_code)


@enforce_types
class CheckNetworkArgParser(ArgParser, NETWORK_Mixin, YAML_Mixin):
    @enforce_types
    def __init__(self, description: str, command_name: str):
        super().__init__(description=description)
        self.add_argument("command", choices=[command_name])
        self.add_argument_YAML()
        self.add_argument_NETWORK()
        self.add_argument(
            "--LOOKBACK_HOURS",
            default=24,
            type=int,
            help="# hours to check back on",
            required=False,
        )


@enforce_types
class GetPredictoorInfoArgParser(ArgParser, CSVDIR_Mixin, NETWORK_Mixin, YAML_Mixin):
    @enforce_types
    def __init__(self, description: str, command_name: str):
        super().__init__(description=description)
        self.add_argument("command", choices=[command_name])
        self.add_argument("PDR_ADDRS", type=str, help="Predictoor address(es)")
        self.add_argument("ST", type=str, help="Start date yyyy-mm-dd")
        self.add_argument("END", type=str, help="End date yyyy-mm-dd")
        self.add_argument_CSVDIR()
        self.add_argument_YAML()
        self.add_argument_NETWORK()


TruevalArgParser = _ArgParser_APPROACH_YAML_NETWORK

DfbuyerArgParser = _ArgParser_YAML_NETWORK

PublisherArgParser = _ArgParser_YAML_NETWORK

TopupArgParser = _ArgParser_YAML_NETWORK
