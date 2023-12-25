import sys
from argparse import ArgumentParser as ArgParser
from argparse import Namespace

from enforce_typing import enforce_types

HELP_LONG = """Predictoor tool

Usage: pdr sim|predictoor|trader|..

Main tools:
  pdr sim PPSS_FILE
  pdr predictoor APPROACH PPSS_FILE NETWORK
  pdr trader APPROACH PPSS_FILE NETWORK
  pdr claim_OCEAN PPSS_FILE
  prd claim_ROSE PPSS_FILE

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


@enforce_types
def print_args(arguments: Namespace):
    arguments_dict = arguments.__dict__
    command = arguments_dict.pop("command", None)

    print(f"dftool {command}: Begin")
    print("Arguments:")

    for arg_k, arg_v in arguments_dict.items():
        print(f"{arg_k}={arg_v}")


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


@enforce_types
class NUM_WALLETS_Mixin:
    def add_argument_NUM_WALLETS(self):
        self.add_argument("--NUM_WALLETS", type=int, help="1|2|..")


@enforce_types
class TO_ADDRESSES_Mixin:
    def add_argument_TO_ADDRESSES(self):
        self.add_argument(
            "TO_ADDRESSES",
            type=str,
            help="Comma-separated list of addresses to send to",
        )


@enforce_types
class TOKEN_AMOUNT_Mixin:
    def add_argument_TOKEN_AMOUNT(self):
        self.add_argument(
            "TOKEN_AMOUNT",
            type=float,
            help="Amount of token to send to each address",
        )


@enforce_types
class NATIVE_TOKEN_Mixin:
    def add_argument_NATIVE_TOKEN(self):
        self.add_argument(
            "--NATIVE_TOKEN",
            action="store_true",
            default=False,
            help="Is native token or OCEAN?"
        )


# ========================================================================
# argparser base classes


@enforce_types
class _ArgParser_PPSS(ArgParser, PPSS_Mixin):
    @enforce_types
    def __init__(self, description: str, command_name: str):
        super().__init__(description=description)
        self.add_argument("command", choices=[command_name])
        self.add_argument_PPSS()


@enforce_types
class _ArgParser_PPSS_NETWORK(ArgParser, PPSS_Mixin, NETWORK_Mixin):
    @enforce_types
    def __init__(self, description: str, command_name: str):
        super().__init__(description=description)
        self.add_argument("command", choices=[command_name])
        self.add_argument_PPSS()
        self.add_argument_NETWORK()


@enforce_types
class _ArgParser_APPROACH_PPSS_NETWORK(
    ArgParser,
    APPROACH_Mixin,
    PPSS_Mixin,
    NETWORK_Mixin,
):
    def __init__(self, description: str, command_name: str):
        super().__init__(description=description)
        self.add_argument("command", choices=[command_name])
        self.add_argument_APPROACH()
        self.add_argument_PPSS()
        self.add_argument_NETWORK()


@enforce_types
class _ArgParser_PPSS_NETWORK_LOOKBACK(
    ArgParser,
    PPSS_Mixin,
    NETWORK_Mixin,
    LOOKBACK_Mixin,
):
    @enforce_types
    def __init__(self, description: str, command_name: str):
        super().__init__(description=description)
        self.add_argument("command", choices=[command_name])
        self.add_argument_PPSS()
        self.add_argument_NETWORK()
        self.add_argument_LOOKBACK()


@enforce_types
class _ArgParser_ST_END_PQDIR_NETWORK_PPSS_PDRS(
    ArgParser,
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
        self.add_argument("command", choices=[command_name])
        self.add_argument_ST()
        self.add_argument_END()
        self.add_argument_PQDIR()
        self.add_argument_PPSS()
        self.add_argument_NETWORK()
        self.add_argument_PDRS()


@enforce_types
class _ArgParser_ST_END_PQDIR_NETWORK_PPSS_FEEDS(
    ArgParser,
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
        self.add_argument("command", choices=[command_name])
        self.add_argument_ST()
        self.add_argument_END()
        self.add_argument_PQDIR()
        self.add_argument_PPSS()
        self.add_argument_NETWORK()
        self.add_argument_FEEDS()


@enforce_types
class _ArgParser_NUM_WALLETS_NETWORK_PPSS(
    ArgParser,
    NUM_WALLETS_Mixin,
    PPSS_Mixin,
    NETWORK_Mixin,
):  # pylint: disable=too-many-ancestors
    @enforce_types
    def __init__(self, description: str, command_name: str):
        super().__init__(description=description)
        self.add_argument("command", choices=[command_name])
        self.add_argument_PPSS()
        self.add_argument_NETWORK()
        self.add_argument_NUM_WALLETS()

@enforce_types
class _ArgParser_FUND_WALLETS_NETWORK_PPSS(
    ArgParser,
    PPSS_Mixin,
    NETWORK_Mixin,
    NATIVE_TOKEN_Mixin,
    TOKEN_AMOUNT_Mixin,
    TO_ADDRESSES_Mixin,
):  # pylint: disable=too-many-ancestors
    @enforce_types
    def __init__(self, description: str, command_name: str):
        super().__init__(description=description)
        self.add_argument("command", choices=[command_name])
        self.add_argument_TOKEN_AMOUNT()
        self.add_argument_TO_ADDRESSES()
        self.add_argument_PPSS()
        self.add_argument_NETWORK()
        self.add_argument_NATIVE_TOKEN()


# ========================================================================
# actual arg-parser implementations are just aliases to argparser base classes
# In order of help text.

SimArgParser = _ArgParser_PPSS

PredictoorArgParser = _ArgParser_APPROACH_PPSS_NETWORK

TraderArgParser = _ArgParser_APPROACH_PPSS_NETWORK

ClaimOceanArgParser = _ArgParser_PPSS

ClaimRoseArgParser = _ArgParser_PPSS


@enforce_types
def do_help_long(status_code=0):
    print(HELP_LONG)
    sys.exit(status_code)


GetPredictoorsInfoArgParser = _ArgParser_ST_END_PQDIR_NETWORK_PPSS_PDRS

GetPredictionsInfoArgParser = _ArgParser_ST_END_PQDIR_NETWORK_PPSS_FEEDS

GetTractionInfoArgParser = _ArgParser_ST_END_PQDIR_NETWORK_PPSS_FEEDS

CheckNetworkArgParser = _ArgParser_PPSS_NETWORK_LOOKBACK

TruevalArgParser = _ArgParser_PPSS_NETWORK

DfbuyerArgParser = _ArgParser_PPSS_NETWORK

PublisherArgParser = _ArgParser_PPSS_NETWORK

TopupArgParser = _ArgParser_PPSS_NETWORK

CreateWalletArgParser = _ArgParser_NUM_WALLETS_NETWORK_PPSS

FundWalletsArgParser = _ArgParser_FUND_WALLETS_NETWORK_PPSS