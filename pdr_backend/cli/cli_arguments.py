import argparse
from argparse import Namespace
import logging
import sys
from typing import List

from enforce_typing import enforce_types
from eth_utils import to_checksum_address

from pdr_backend.cli.nested_arg_parser import NestedArgParser

logger = logging.getLogger("cli")

HELP_TOP = """Predictoor tool

Usage: pdr sim|predictoor|trader|..
"""

HELP_MAIN = """
Main tools:
  pdr sim PPSS_FILE
  pdr predictoor PPSS_FILE NETWORK
  pdr trader APPROACH PPSS_FILE NETWORK
  pdr claim_OCEAN PPSS_FILE
  pdr claim_ROSE PPSS_FILE
"""

HELP_HELP = """
Detailed help:
  pdr <cmd> -h
  pdr help_long
"""

HELP_SIGN = """
Transactions are signed with envvar 'PRIVATE_KEY`.
"""

HELP_DOT = """
To pass args down to ppss, use dot notation.
Example: pdr lake ppss.yaml sapphire-mainnet --lake_ss.st_timestr=2023-01-01 --lake_ss.fin_timestr=2023-12-31
"""

HELP_OTHER_TOOLS = """
Power tools:
  pdr multisim PPSS_FILE
  pdr deployer (for >1 predictoor bots)
  pdr lake PPSS_FILE NETWORK
  pdr analytics PPSS_FILE NETWORK

Utilities:
  pdr get_predictoors_info ST END PQDIR PPSS_FILE NETWORK --PDRS
  pdr get_predictions_info ST END PQDIR PPSS_FILE NETWORK --FEEDS
  pdr get_traction_info ST END PQDIR PPSS_FILE NETWORK --FEEDS
  pdr check_network PPSS_FILE NETWORK --LOOKBACK_HOURS
  pdr create_accounts NUM PPSS_FILE NETWORK
  pdr print_balances ACCOUNT PPSS_FILE NETWORK
  pdr fund_accounts TOKEN_AMOUNT ACCOUNTS PPSS_FILE NETWORK --NATIVE_TOKEN
  pdr deploy_pred_submitter_mgr PPSS_FILE NETWORK

Tools for core team:
  pdr trueval PPSS_FILE NETWORK
  pdr dfbuyer PPSS_FILE NETWORK
  pdr publisher PPSS_FILE NETWORK
  pdr topup PPSS_FILE NETWORK
  pytest, black, mypy, pylint, ..
"""

HELP_SHORT = HELP_TOP + HELP_MAIN + HELP_HELP + HELP_SIGN

HELP_LONG = HELP_TOP + HELP_MAIN + HELP_HELP + HELP_OTHER_TOOLS + HELP_SIGN + HELP_DOT


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
def check_addresses(value) -> List[str]:
    """
    @description
        Validates that all addresses is a comma-separated list of strings
        Each string must be a valid Ethereum address

    @return
        checksummed list of addresses
    """
    if not value:
        return []
    addrs = value.split(",")
    return [check_address(addr) for addr in addrs]


@enforce_types
def check_address(addr) -> str:
    """
    @description
        Validates the input address a string, with a valid eth address

    @return
        checksummed version of the address
    """
    try:
        addr2 = to_checksum_address(addr.lower())
    except Exception as exc:
        raise TypeError(f"{addr} is not a valid Ethereum address") from exc

    return addr2


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
class ACCOUNT_Mixin:
    def add_argument_ACCOUNT(self):
        self.add_argument(
            "ACCOUNT",
            type=check_address,
            help="Valid ethereum address",
        )


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
class _ArgParser_ACCOUNT_PPSS_NETWORK(
    CustomArgParser,
    ACCOUNT_Mixin,
    PPSS_Mixin,
    NETWORK_Mixin,
):  # pylint: disable=too-many-ancestors
    @enforce_types
    def __init__(self, description: str, command_name: str):
        super().__init__(description=description)
        self.add_arguments_bulk(command_name, ["ACCOUNT", "PPSS", "NETWORK"])


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


@enforce_types
class _ArgParser_DEPLOYER:
    def __init__(self) -> None:
        self.parser = argparse.ArgumentParser(
            prog="pdr",
            description="Generate and manage agent deployments",
        )
        self.parser.add_argument(
            "command", choices=["deployer"], help="The deployer command"
        )

        self.subparsers = self.parser.add_subparsers(
            dest="subcommand", help="sub-command help"
        )

        self._add_generate_parser()
        self._add_deploy_parser()
        self._add_destroy_parser()
        self._add_logs_parser()
        self._add_build_parser()
        self._add_push_parser()
        self._add_remote_registry()

    def parse_args(self):
        return self.parser.parse_args()

    def parse_known_args(self):
        return self.parser.parse_known_args()

    def _add_generate_parser(self):
        parser_generate = self.subparsers.add_parser("generate", help="generate help")
        parser_generate.add_argument(
            "config_path", help="Path to the configuration file"
        )
        parser_generate.add_argument("config_name", help="Name of the configuration")
        parser_generate.add_argument(
            "deployment_method",
            help="Method of deployment",
            choices=["k8s"],
        )
        parser_generate.add_argument(
            "output_dir", help="Output directory for the generated files"
        )

    def _add_deploy_parser(self):
        parser_deploy = self.subparsers.add_parser("deploy", help="deploy help")
        self._add_remote_parsers(parser_deploy)

    def _add_destroy_parser(self):
        parser_destroy = self.subparsers.add_parser("destroy", help="destroy help")
        self._add_remote_parsers(parser_destroy)

    def _add_remote_registry(self):
        parser_deploy = self.subparsers.add_parser(
            "registry", help="deploy_registry help"
        )
        parser_deploy.add_argument(
            "action", help="Action", choices=["deploy", "destroy", "auth", "url"]
        )
        parser_deploy.add_argument("registry_name", help="Registry name")
        self._add_remote_parsers(parser_deploy, False)

    def _add_logs_parser(self):
        parser_logs = self.subparsers.add_parser("logs", help="logs help")
        self._add_remote_parsers(parser_logs)

    def _add_build_parser(self):
        parser_build = self.subparsers.add_parser("build", help="build help")
        parser_build.add_argument(
            "image_name", help="Image name", default="pdr_backend"
        )
        parser_build.add_argument("image_tag", help="Image tag", default="deployer")

    def _add_push_parser(self):
        parser_push = self.subparsers.add_parser("push", help="push help")
        parser_push.add_argument("registry_name", help="Registry name")
        parser_push.add_argument("image_name", help="Image name", default="pdr_backend")
        parser_push.add_argument("image_tag", help="Image tag", default="deployer")

    def _add_remote_parsers(self, subparser, with_config=True):
        if with_config:
            subparser.add_argument("config_name", help="Name of the configuration")
        subparser.add_argument(
            "-p",
            "--provider",
            help="Cloud provider",
            required=False,
            choices=["aws", "azure", "gcp"],
        )
        subparser.add_argument(
            "-r",
            "--region",
            required=False,
            help="Deployment zone/region",
        )
        subparser.add_argument(
            "--project_id",
            help="Google Cloud project id",
            required=False,
        )
        subparser.add_argument(
            "--resource_group",
            help="Azure resource group",
            required=False,
        )


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

# main tools
SimArgParser = _ArgParser_PPSS
PredictoorArgParser = _ArgParser_PPSS_NETWORK
TraderArgParser = _ArgParser_APPROACH_PPSS_NETWORK
ClaimOceanArgParser = _ArgParser_PPSS
ClaimRoseArgParser = _ArgParser_PPSS

# power tools
MultisimArgParser = _ArgParser_PPSS
DeployerArgPaser = _ArgParser_DEPLOYER
LakeArgParser = _ArgParser_PPSS_NETWORK
AnalyticsArgParser = _ArgParser_PPSS_NETWORK

# utilities
GetPredictoorsInfoArgParser = _ArgParser_ST_END_PQDIR_NETWORK_PPSS_PDRS
GetPredictionsInfoArgParser = _ArgParser_ST_END_PQDIR_NETWORK_PPSS_FEEDS
GetTractionInfoArgParser = _ArgParser_ST_END_PQDIR_NETWORK_PPSS_FEEDS
CheckNetworkArgParser = _ArgParser_PPSS_NETWORK_LOOKBACK
CreateAccountsArgParser = _ArgParser_NUM_PPSS_NETWORK
PrintBalancesArgParser = _ArgParser_ACCOUNT_PPSS_NETWORK
FundAccountsArgParser = _ArgParser_FUND_ACCOUNTS_PPSS_NETWORK

# Tools for core team
TruevalArgParser = _ArgParser_PPSS_NETWORK
DfbuyerArgParser = _ArgParser_PPSS_NETWORK
PublisherArgParser = _ArgParser_PPSS_NETWORK


class TopupArgParser(_ArgParser_PPSS_NETWORK):
    @property
    def network_choices(self):
        return ["sapphire-testnet", "sapphire-mainnet"]


# below, list each entry in defined_parsers in same order as HELP_LONG
defined_parsers = {
    # main tools
    "do_sim": SimArgParser("Run simulation", "sim"),
    "do_predictoor": PredictoorArgParser("Run a predictoor bot", "predictoor"),
    "do_trader": TraderArgParser("Run a trader bot", "trader"),
    "do_claim_OCEAN": ClaimOceanArgParser("Claim OCEAN", "claim_OCEAN"),
    "do_claim_ROSE": ClaimRoseArgParser("Claim ROSE", "claim_ROSE"),
    # power tools
    "do_multisim": MultisimArgParser("Run >1 simulations", "multisim"),
    "do_deployer": DeployerArgPaser(),
    "do_lake": LakeArgParser("Run the lake tool", "lake"),
    "do_analytics": AnalyticsArgParser("Run the analytics tool", "analytics"),
    "do_deploy_pred_submitter_mgr": _ArgParser_PPSS_NETWORK(
        "Deploy prediction submitter manager contract", "deploy_pred_submitter_mgr"
    ),
    # utilities
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
    "do_create_accounts": CreateAccountsArgParser(
        "Create multiple accounts..", "create_accounts"
    ),
    "do_print_balances": PrintBalancesArgParser(
        "View balances of an account", "print_balances"
    ),
    "do_fund_accounts": FundAccountsArgParser(
        "Fund multiple wallets from a single address", "fund_accounts"
    ),
    # tools for core team
    "do_trueval": TruevalArgParser("Run trueval bot", "trueval"),
    "do_dfbuyer": DfbuyerArgParser("Run dfbuyer bot", "dfbuyer"),
    "do_publisher": PublisherArgParser("Publish feeds", "publisher"),
    "do_topup": TopupArgParser("Topup OCEAN and ROSE in dfbuyer, trueval, ..", "topup"),
}


def get_arg_parser(func_name):
    if func_name not in defined_parsers:
        raise ValueError(f"Unknown function name: {func_name}")

    return defined_parsers[func_name]
