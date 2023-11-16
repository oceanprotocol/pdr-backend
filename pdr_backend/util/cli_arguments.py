from argparse import ArgumentParser as ArgParser
from argparse import Namespace
import os
import sys

from enforce_typing import enforce_types

# ========================================================================
HELP_LONG = """Predictoor tool

Usage: pdr sim|predictoor|trader|..

  pdr sim --YAML_FILE
  pdr predictoor PREDICTOOR_APPROACH NETWORK --YAML_FILE
  pdr trader TRADER_APPROACH NETWORK --YAML_FILE
  pdr claim CLAIM_TOKEN
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
def print_arguments(arguments: Namespace):
    arguments_dict = arguments.__dict__
    command = arguments_dict.pop("command", None)

    print(f"dftool {command}: Begin")
    print("Arguments:")

    for arg_k, arg_v in arguments_dict.items():
        print(f"{arg_k}={arg_v}")

        
@enforce_types
class YAML_FILE_Mixin:
    def add_argument_YAML_FILE()
        self.add_argument(
            "--YAML_FILE",
            default="ppss.yaml",
            type=str,
            help="Settings file",
            required=False,
        )

        
@enforce_types
class YAML_FILE_Mixin:
    def add_argument_NETWORK()
        self.add_argument(
            "NETWORK",
            type=str,
            help="sapphire-testnet|sapphire-mainnet|barge-pdr|barge-pytest",
            required=True,
        )

        
@enforce_types
class SimArgParser(ArgParser, YAML_FILE_Mixin):
    @enforce_types
    def __init__(self, description: str, command_name: str):
        super().__init__(description=description)
        self.add_argument("command", choices=[command_name])
        self.add_argument_YAML_FILE()

        
@enforce_types
class PredictoorArgParser(ArgParser, NETWORK_Mixin, YAML_FILE_Mixin):
    @enforce_types
    def __init__(self, description: str, command_name: str):
        super().__init__(description=description)
        self.add_argument("command", choices=[command_name])
        self.add_argument("PREDICTOOR_APPROACH", type=int, help="1|2|3")
        self.add_argument_NETWORK()
        self.add_argument_YAML_FILE()

        
@enforce_types
class TraderArgParser(ArgParser, NETWORK_Mixin, YAML_FILE_Mixin):
    @enforce_types
    def __init__(self, description: str, command_name: str):
        super().__init__(description=description)
        self.add_argument("command", choices=[command_name])
        self.add_argument("TRADER_APPROACH", type=int, help="1|2")
        self.add_argument_NETWORK()
        self.add_argument_YAML_FILE()

        
@enforce_types
class ClaimArgParser(ArgParser):
    @enforce_types
    def __init__(self, description: str, command_name: str):
        super().__init__(description=description)
        self.add_argument("command", choices=[command_name])
        self.add_argument("CLAIM_TOKEN", type=str, help="OCEAN|ROSE")

        
@enforce_types
class _ArgParser_NETWORK_YAML_FILE(ArgParser, NETWORK_Mixin, YAML_FILE_Mixin):
    @enforce_types
    def __init__(self, description: str, command_name: str):
        super().__init__(description=description)
        self.add_argument("command", choices=[command_name])
        self.add_argument_NETWORK()
        self.add_argument_YAML_FILE()

        
@enforce_types
class TruevalArgParser(ArgParser, _ArgParser_NETWORK_YAML_FILE):
    pass


@enforce_types
class DfBuyerArgParser(ArgParser, _ArgParser_NETWORK_YAML_FILE):
    pass


@enforce_types
class PublisherArgParser(ArgParser, _ArgParser_NETWORK_YAML_FILE):
    pass
   
