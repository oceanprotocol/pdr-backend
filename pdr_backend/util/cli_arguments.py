from argparse import ArgumentParser as ArgParser
from argparse import Namespace
import os
import sys

from enforce_typing import enforce_types

# ========================================================================
HELP_LONG = """Predictoor tool

Usage: pdr sim|predictoor|trader|..

  pdr sim --YAML_FILE
  pdr predictoor APPROACH NETWORK --YAML_FILE
  pdr trader APPROACH NETWORK --YAML_FILE
  pdr claim_OCEAN
  prd claim_ROSE
  pdr help

Transactions are signed with envvar 'PRIVATE_KEY`.

Tools for core team:
  pdr trueval NETWORK --YAML_FILE
  pdr dfbuyer NETWORK --YAML_FILE
  pdr publisher NETWORK --YAML_FILE
"""



@enforce_types
def do_help_long(status_code=0):
    print(HELP_LONG)
    sys.exit(status_code)

    
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
        self.add_argument(
            "--YAML_FILE",
            default="ppss.yaml",
            type=str,
            help="Settings file",
            required=False,
        )

        
@enforce_types
class APPROACH_Mixin:
    def add_argument_APPROACH(self):
        self.add_argument("APPROACH", type=int, help="1|2|..")

        
@enforce_types
class NETWORK_Mixin:
    def add_argument_NETWORK(self):
        self.add_argument(
            "NETWORK",
            type=str,
            help="sapphire-testnet|sapphire-mainnet|barge-pdr|barge-pytest"
            )

        
@enforce_types
class SimArgParser(ArgParser, YAML_Mixin):
    def __init__(self, description: str, command_name: str):
        super().__init__(description=description)
        self.add_argument("command", choices=[command_name])
        self.add_argument_YAML()

        
@enforce_types
class _ArgParser_APPROACH_NETWORK_YAML(
        ArgParser,
        APPROACH_Mixin,
        NETWORK_Mixin,
        YAML_Mixin,
):
    def __init__(self, description: str, command_name: str):
        super().__init__(description=description)
        self.add_argument("command", choices=[command_name])
        self.add_argument_APPROACH()
        self.add_argument_NETWORK()
        self.add_argument_YAML()

PredictoorArgParser = _ArgParser_APPROACH_NETWORK_YAML
TraderArgParser = _ArgParser_APPROACH_NETWORK_YAML

        
@enforce_types
class _ArgParser_NETWORK_YAML(ArgParser, NETWORK_Mixin, YAML_Mixin):
    @enforce_types
    def __init__(self, description: str, command_name: str):
        super().__init__(description=description)
        self.add_argument("command", choices=[command_name])
        self.add_argument_NETWORK()
        self.add_argument_YAML()

TruevalArgParser =  _ArgParser_NETWORK_YAML
DfbuyerArgParser = _ArgParser_NETWORK_YAML
PublisherArgParser = _ArgParser_NETWORK_YAML


