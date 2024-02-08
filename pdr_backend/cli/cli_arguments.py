import sys
from argparse import Namespace

from enforce_typing import enforce_types

from eth_utils import to_checksum_address

from pdr_backend.cli.nested_arg_parser import NestedArgParser

HELP_LONG = """Predictoor tool
  Transactions are signed with envvar 'PRIVATE_KEY`.

Usage: pdr sim|predictoor|trader|..

Main tools:
  pdr sim PPSS_FILE
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
  pdr create_accounts NUM PPSS_FILE NETWORK
  pdr view_accounts ACCOUNTS PPSS_FILE NETWORK
  pdr fund_accounts TOKEN_AMOUNT ACCOUNTS PPSS_FILE NETWORK --NATIVE_TOKEN

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
        if hasattr(self, "network_choices"):
            self.add_argument(
                "NETWORK",
                type=str,
                choices=self.network_choices,
                help="|".join(self.network_choices),
            )
        else:
            self.add_argument(
                "NETWORK",
                type=str,
                help="sapphire-testnet|sapphire-mainnet|development|barge-pytest|..",
            )


@enforce_types
def check_addresses(value):
    """
    @description
        validates that all addressses is a comma-separated list of strings
        each string, will be a valid Ethereum address
    """
    if not value:
        return []

    addresses = value.split(",")
    checksummed_addresses = []
    for address in addresses:
        try:
            checksummed_addresses.append(to_checksum_address(address.lower()))
        except Exception as exc:
            raise TypeError(f"{address} is not a valid Ethereum address") from exc
    return checksummed_addresses


@enforce_types
class PDRS_Mixin:
    def add_argument_PDRS(self):
        self.add_argument(
            "--PDRS",
            type=check_addresses,
            help="Predictoor address(es), separated by comma. If not specified, uses all.",
            required=False,
        )


@enforce_types
class FEEDS_Mixin:
    def add_argument_FEEDS(self):
        self.add_argument(
            "--FEEDS",
            type=check_addresses,
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
def check_positive(value):
    try:
        ivalue = int(value)
    except Exception as exc:
        raise TypeError("%s is not a valid int" % value) from exc

    try:
        if ivalue <= 0:
            raise Exception("Zero or below.")
    except Exception as exc:
        raise TypeError("%s is an invalid positive int value" % value) from exc

    return ivalue


@enforce_types
class NUM_Mixin:
    def add_argument_NUM(self):
        self.add_argument("NUM", type=check_positive)


@enforce_types
class ACCOUNTS_Mixin:
    def add_argument_ACCOUNTS(self):
        self.add_argument(
            "ACCOUNTS",
            type=check_addresses,
            help="Comma-separated list of valid ethereum addresses",
        )


@enforce_types
class TOKEN_AMOUNT_Mixin:
    def add_argument_TOKEN_AMOUNT(self):
        self.add_argument(
            "TOKEN_AMOUNT",
            type=float,
            help="Amount of token to send to each address (in 1e18, ether)",
        )


@enforce_types
class NATIVE_TOKEN_Mixin:
    def add_argument_NATIVE_TOKEN(self):
        self.add_argument(
            "--NATIVE_TOKEN",
            action="store_true",
            default=False,
            help="If --NATIVE_TOKEN then transact with ROSE otherwise use OCEAN",
        )


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
class _ArgParser_PPSS_NETWORK(CustomArgParser, PPSS_Mixin, NETWORK_Mixin):
    @enforce_types
    def __init__(self, description: str, command_name: str):
        super().__init__(description=description)
        self.add_arguments_bulk(command_name, ["PPSS", "NETWORK"])


@enforce_types
# pylint: disable=too-many-ancestors
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
# pylint: disable=too-many-ancestors
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


@enforce_types
class _ArgParser_NUM_PPSS_NETWORK(
    CustomArgParser,
    NUM_Mixin,
    PPSS_Mixin,
    NETWORK_Mixin,
):  # pylint: disable=too-many-ancestors
    @enforce_types
    def __init__(self, description: str, command_name: str):
        super().__init__(description=description)
        self.add_arguments_bulk(command_name, ["NUM", "PPSS", "NETWORK"])


@enforce_types
class _ArgParser_ACCOUNTS_PPSS_NETWORK(
    CustomArgParser,
    ACCOUNTS_Mixin,
    PPSS_Mixin,
    NETWORK_Mixin,
):  # pylint: disable=too-many-ancestors
    @enforce_types
    def __init__(self, description: str, command_name: str):
        super().__init__(description=description)
        self.add_arguments_bulk(command_name, ["ACCOUNTS", "PPSS", "NETWORK"])


@enforce_types
class _ArgParser_FUND_ACCOUNTS_PPSS_NETWORK(
    CustomArgParser,
    TOKEN_AMOUNT_Mixin,
    ACCOUNTS_Mixin,
    PPSS_Mixin,
    NETWORK_Mixin,
    NATIVE_TOKEN_Mixin,
):  # pylint: disable=too-many-ancestors
    @enforce_types
    def __init__(self, description: str, command_name: str):
        super().__init__(description=description)
        self.add_argument("command", choices=[command_name])
        self.add_arguments_bulk(
            command_name,
            ["TOKEN_AMOUNT", "ACCOUNTS", "PPSS", "NETWORK", "NATIVE_TOKEN"],
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


SimArgParser = _ArgParser_PPSS

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


class TopupArgParser(_ArgParser_PPSS_NETWORK):
    @property
    def network_choices(self):
        return ["sapphire-testnet", "sapphire-mainnet"]


CreateAccountsArgParser = _ArgParser_NUM_PPSS_NETWORK

AccountsArgParser = _ArgParser_ACCOUNTS_PPSS_NETWORK

FundAccountsArgParser = _ArgParser_FUND_ACCOUNTS_PPSS_NETWORK

defined_parsers = {
    "do_sim": SimArgParser("Run simulation", "sim"),
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
    "do_create_accounts": CreateAccountsArgParser(
        "Create multiple accounts..", "create_accounts"
    ),
    "do_view_accounts": AccountsArgParser(
        "View balances from 1 or more accounts", "view_accounts"
    ),
    "do_fund_accounts": FundAccountsArgParser(
        "Fund multiple wallets from a single address", "fund_accounts"
    ),
}


def get_arg_parser(func_name):
    if func_name not in defined_parsers:
        raise ValueError(f"Unknown function name: {func_name}")

    return defined_parsers[func_name]
