import sys

from enforce_typing import enforce_types
from pdr_backend.dfbuyer.dfbuyer_agent import DFBuyerAgent

from pdr_backend.ppss.ppss import PPSS
from pdr_backend.publisher.publish_assets import publish_assets
from pdr_backend.sim.sim_engine import SimEngine
from pdr_backend.payout.payout import do_ocean_payout, do_rose_payout
from pdr_backend.predictoor.approach1.predictoor_agent1 import PredictoorAgent1
from pdr_backend.predictoor.approach3.predictoor_agent3 import PredictoorAgent3
from pdr_backend.trader.approach1.trader_agent1 import TraderAgent1
from pdr_backend.trader.approach2.trader_agent2 import TraderAgent2
from pdr_backend.trueval.trueval_agent import TruevalAgent
from pdr_backend.util.check_network import check_network_main
from pdr_backend.util.fund_accounts import fund_accounts_with_OCEAN

from pdr_backend.util.cli_arguments import (
    ClaimOceanArgParser,
    ClaimRoseArgParser,
    CheckNetworkArgParser,
    DfbuyerArgParser,
    do_help_long,
    GetPredictoorsInfoArgParser,
    GetPredictionsInfoArgParser,
    GetTractionInfoArgParser,
    PredictoorArgParser,
    print_args,
    PublisherArgParser,
    SimArgParser,
    TopupArgParser,
    TraderArgParser,
    TruevalArgParser,
)

from pdr_backend.util.contract import get_address
from pdr_backend.analytics.get_predictions_info import get_predictions_info_main
from pdr_backend.analytics.get_predictoors_info import get_predictoors_info_main
from pdr_backend.analytics.get_traction_info import get_traction_info_main
from pdr_backend.util.topup import topup_main


@enforce_types
def _do_main():
    if len(sys.argv) <= 1 or sys.argv[1] == "help":
        do_help_long(0)

    func_name = f"do_{sys.argv[1]}"
    func = globals().get(func_name)
    if func is None:
        do_help_long(1)

    func()


# ========================================================================
# actual cli implementations. In order of help text.


@enforce_types
def do_sim():
    parser = SimArgParser("Run simulation", "sim")
    args = parser.parse_args()
    print_args(args)

    ppss = PPSS(yaml_filename=args.PPSS_FILE, network="development")
    sim_engine = SimEngine(ppss)
    sim_engine.run()


@enforce_types
def do_predictoor():
    parser = PredictoorArgParser("Run a predictoor bot", "predictoor")
    args = parser.parse_args()
    print_args(args)

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
def do_trader():
    parser = TraderArgParser("Run a trader bot", "trader")
    args = parser.parse_args()
    print_args(args)

    ppss = PPSS(yaml_filename=args.PPSS_FILE, network=args.NETWORK)
    approach = args.APPROACH

    if approach == 1:
        agent = TraderAgent1(ppss)
    elif approach == 2:
        agent = TraderAgent2(ppss)
    else:
        raise ValueError(f"Unknown trader approach {approach}")

    agent.run()


# do_help() is implemented in cli_arguments and imported, so nothing needed here


@enforce_types
def do_claim_OCEAN():
    parser = ClaimOceanArgParser("Claim OCEAN", "claim_OCEAN")
    args = parser.parse_args()
    print_args(args)

    ppss = PPSS(yaml_filename=args.PPSS_FILE, network="sapphire-mainnet")
    do_ocean_payout(ppss)


@enforce_types
def do_claim_ROSE():
    parser = ClaimRoseArgParser("Claim ROSE", "claim_ROSE")
    args = parser.parse_args()
    print_args(args)

    ppss = PPSS(yaml_filename=args.PPSS_FILE, network="sapphire-mainnet")
    do_rose_payout(ppss)


@enforce_types
def do_get_predictoors_info():
    parser = GetPredictoorsInfoArgParser(
        "For specified predictoors, report {accuracy, ..} of each predictoor",
        "get_predictoors_info",
    )
    args = parser.parse_args()
    print_args(args)

    ppss = PPSS(yaml_filename=args.PPSS_FILE, network=args.NETWORK)
    get_predictoors_info_main(ppss, args.PDRS, args.ST, args.END, args.PQDIR)


@enforce_types
def do_get_predictions_info():
    parser = GetPredictionsInfoArgParser(
        "For specified feeds, report {accuracy, ..} of each predictoor",
        "get_predictions_info",
    )
    args = parser.parse_args()
    print_args(args)

    ppss = PPSS(yaml_filename=args.PPSS_FILE, network=args.NETWORK)
    get_predictions_info_main(ppss, args.FEEDS, args.ST, args.END, args.PQDIR)


@enforce_types
def do_get_traction_info():
    parser = GetTractionInfoArgParser(
        "Get traction info: # predictoors vs time, etc",
        "get_traction_info",
    )
    args = parser.parse_args()
    print_args(args)

    ppss = PPSS(yaml_filename=args.PPSS_FILE, network=args.NETWORK)
    get_traction_info_main(ppss, args.ST, args.END, args.PQDIR)


@enforce_types
def do_check_network():
    parser = CheckNetworkArgParser("Check network", "check_network")
    args = parser.parse_args()
    print_args(args)

    ppss = PPSS(yaml_filename=args.PPSS_FILE, network=args.NETWORK)
    check_network_main(ppss, args.LOOKBACK_HOURS)


@enforce_types
def do_trueval(testing=False):
    parser = TruevalArgParser("Run trueval bot", "trueval")
    args = parser.parse_args()
    print_args(args)

    ppss = PPSS(yaml_filename=args.PPSS_FILE, network=args.NETWORK)
    predictoor_batcher_addr = get_address(ppss.web3_pp, "PredictoorHelper")
    agent = TruevalAgent(ppss, predictoor_batcher_addr)

    agent.run(testing)


# @enforce_types
def do_dfbuyer():
    parser = DfbuyerArgParser("Run dfbuyer bot", "dfbuyer")
    args = parser.parse_args()
    print_args(args)

    ppss = PPSS(yaml_filename=args.PPSS_FILE, network=args.NETWORK)
    agent = DFBuyerAgent(ppss)
    agent.run()


@enforce_types
def do_publisher():
    parser = PublisherArgParser("Publish feeds", "publisher")
    args = parser.parse_args()
    print_args(args)

    ppss = PPSS(yaml_filename=args.PPSS_FILE, network=args.NETWORK)
    if ppss.web3_pp.network == "development":
        fund_accounts_with_OCEAN(ppss.web3_pp)
    publish_assets(ppss.web3_pp, ppss.publisher_ss)


@enforce_types
def do_topup():
    parser = TopupArgParser("Topup OCEAN and ROSE in dfbuyer, trueval, ..", "topup")
    args = parser.parse_args()
    print_args(args)

    ppss = PPSS(yaml_filename=args.PPSS_FILE, network=args.NETWORK)
    topup_main(ppss)
