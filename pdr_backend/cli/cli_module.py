import sys

from enforce_typing import enforce_types

from pdr_backend.analytics.check_network import check_network_main
from pdr_backend.analytics.get_predictions_info import get_predictions_info_main
from pdr_backend.analytics.get_predictoors_info import get_predictoors_info_main
from pdr_backend.analytics.get_traction_info import get_traction_info_main
from pdr_backend.cli.cli_arguments import (
    do_help_long,
    get_arg_parser,
    print_args,
)
from pdr_backend.dfbuyer.dfbuyer_agent import DFBuyerAgent
from pdr_backend.lake.ohlcv_data_factory import OhlcvDataFactory
from pdr_backend.payout.payout import do_ocean_payout, do_rose_payout
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.predictoor.approach1.predictoor_agent1 import PredictoorAgent1
from pdr_backend.predictoor.approach3.predictoor_agent3 import PredictoorAgent3
from pdr_backend.publisher.publish_assets import publish_assets
from pdr_backend.xpmt.xpmt_engine import XpmtEngine
from pdr_backend.trader.approach1.trader_agent1 import TraderAgent1
from pdr_backend.trader.approach2.trader_agent2 import TraderAgent2
from pdr_backend.trueval.trueval_agent import TruevalAgent
from pdr_backend.util.contract import get_address
from pdr_backend.util.fund_accounts import fund_accounts_with_OCEAN
from pdr_backend.util.topup import topup_main


@enforce_types
def _do_main():
    if len(sys.argv) <= 1 or sys.argv[1] == "help":
        do_help_long(0)

    func_name = f"do_{sys.argv[1]}"
    func = globals().get(func_name)
    if func is None:
        do_help_long(1)

    parser = get_arg_parser(func_name)
    args = parser.parse_args()
    print_args(args)

    func(args)


# ========================================================================
# actual cli implementations. In order of help text.


@enforce_types
def do_xpmt(args):
    ppss = PPSS(yaml_filename=args.PPSS_FILE, network="development")
    xpmt_engine = XpmtEngine(ppss)
    xpmt_engine.run()


@enforce_types
def do_predictoor(args):
    ppss = PPSS(yaml_filename=args.PPSS_FILE, network=args.NETWORK)

    approach = args.APPROACH
    if approach == 1:
        agent = PredictoorAgent1(ppss)

    elif approach == 3:
        agent = PredictoorAgent3(ppss)

    else:
        raise ValueError(f"Unknown predictoor approach {approach}")

    agent.run()


@enforce_types
def do_trader(args):
    ppss = PPSS(yaml_filename=args.PPSS_FILE, network=args.NETWORK)
    approach = args.APPROACH

    if approach == 1:
        agent = TraderAgent1(ppss)
    elif approach == 2:
        agent = TraderAgent2(ppss)
    else:
        raise ValueError(f"Unknown trader approach {approach}")

    agent.run()


@enforce_types
def do_lake(args):
    ppss = PPSS(yaml_filename=args.PPSS_FILE, network=args.NETWORK)
    ohlcv_data_factory = OhlcvDataFactory(ppss.lake_ss)
    df = ohlcv_data_factory.get_mergedohlcv_df()
    print(df)


# do_help() is implemented in cli_arguments and imported, so nothing needed here


@enforce_types
def do_claim_OCEAN(args):
    ppss = PPSS(yaml_filename=args.PPSS_FILE, network="sapphire-mainnet")
    do_ocean_payout(ppss)


@enforce_types
def do_claim_ROSE(args):
    ppss = PPSS(yaml_filename=args.PPSS_FILE, network="sapphire-mainnet")
    do_rose_payout(ppss)


@enforce_types
def do_get_predictoors_info(args):
    ppss = PPSS(yaml_filename=args.PPSS_FILE, network=args.NETWORK)
    get_predictoors_info_main(ppss, args.ST, args.END, args.PDRS)


@enforce_types
def do_get_predictions_info(args):
    ppss = PPSS(yaml_filename=args.PPSS_FILE, network=args.NETWORK)
    get_predictions_info_main(ppss, args.ST, args.END, args.FEEDS)


@enforce_types
def do_get_traction_info(args):
    ppss = PPSS(yaml_filename=args.PPSS_FILE, network=args.NETWORK)
    get_traction_info_main(ppss, args.ST, args.END, args.PQDIR)


@enforce_types
def do_check_network(args):
    ppss = PPSS(yaml_filename=args.PPSS_FILE, network=args.NETWORK)
    check_network_main(ppss, args.LOOKBACK_HOURS)


@enforce_types
def do_trueval(args, testing=False):
    ppss = PPSS(yaml_filename=args.PPSS_FILE, network=args.NETWORK)
    predictoor_batcher_addr = get_address(ppss.web3_pp, "PredictoorHelper")
    agent = TruevalAgent(ppss, predictoor_batcher_addr)

    agent.run(testing)


# @enforce_types
def do_dfbuyer(args):
    ppss = PPSS(yaml_filename=args.PPSS_FILE, network=args.NETWORK)
    agent = DFBuyerAgent(ppss)
    agent.run()


@enforce_types
def do_publisher(args):
    ppss = PPSS(yaml_filename=args.PPSS_FILE, network=args.NETWORK)

    if ppss.web3_pp.network == "development":
        fund_accounts_with_OCEAN(ppss.web3_pp)
    publish_assets(ppss.web3_pp, ppss.publisher_ss)


@enforce_types
def do_topup(args):
    ppss = PPSS(yaml_filename=args.PPSS_FILE, network=args.NETWORK)
    topup_main(ppss)
