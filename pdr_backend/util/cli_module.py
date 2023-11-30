import os
import sys

from enforce_typing import enforce_types
from pdr_backend.dfbuyer.dfbuyer_agent import DFBuyerAgent

from pdr_backend.ppss.ppss import PPSS
from pdr_backend.publisher.main import publish_assets
from pdr_backend.sim.sim_engine import SimEngine
from pdr_backend.payout.payout import do_ocean_payout, do_rose_payout
from pdr_backend.predictoor.approach1.predictoor_agent1 import PredictoorAgent1
from pdr_backend.predictoor.approach3.predictoor_agent3 import PredictoorAgent3
from pdr_backend.trader.approach1.trader_agent1 import TraderAgent1
from pdr_backend.trader.approach2.trader_agent2 import TraderAgent2

from pdr_backend.trueval.trueval_agent_base import get_trueval
from pdr_backend.trueval.trueval_agent_batch import TruevalAgentBatch
from pdr_backend.trueval.trueval_agent_single import TruevalAgentSingle
from pdr_backend.util.check_network import check_network_main

from pdr_backend.util.cli_arguments import (
    ClaimOceanArgParser,
    ClaimRoseArgParser,
    CheckNetworkArgParser,
    DfbuyerArgParser,
    do_help_long,
    GetPredictoorInfoArgParser,
    GetSystemInfoArgParser,
    PredictoorArgParser,
    print_args,
    PublisherArgParser,
    SimArgParser,
    TraderArgParser,
    TruevalArgParser,
)

from pdr_backend.util.contract import get_address
from pdr_backend.util.get_predictoor_info import get_predictoor_info_main
from pdr_backend.util.get_system_info import get_system_info_main
from pdr_backend.util.subgraph_predictions import get_all_contract_ids_by_owner
from pdr_backend.util.topup import topup_main


@enforce_types
def _do_main():
    os.environ.pop("NETWORK_OVERRIDE", None)  # disallow override in CLI
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

    ppss = PPSS(yaml_filename=args.YAML_FILE, network="development")
    sim_engine = SimEngine(ppss)
    sim_engine.run()


@enforce_types
def do_predictoor():
    parser = PredictoorArgParser("Run a predictoor bot", "predictoor")
    args = parser.parse_args()
    print_args(args)

    ppss = PPSS(yaml_filename=args.YAML_FILE, network=args.NETWORK)

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

    ppss = PPSS(yaml_filename=args.YAML_FILE, network=args.NETWORK)
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

    ppss = PPSS(yaml_filename=args.YAML_FILE, network="sapphire_mainnet")
    do_ocean_payout(ppss)


@enforce_types
def do_claim_ROSE():
    parser = ClaimRoseArgParser("Claim ROSE", "claim_ROSE")
    args = parser.parse_args()
    print_args(args)

    ppss = PPSS(yaml_filename=args.YAML_FILE, network="sapphire_mainnet")
    do_rose_payout(ppss)


@enforce_types
def do_get_predictoor_info():
    parser = GetPredictoorInfoArgParser("Get predictoor info", "get_predictoor_info")
    args = parser.parse_args()
    print_args(args)

    ppss = PPSS(yaml_filename=args.YAML_FILE, network=args.NETWORK)
    get_predictoor_info_main(ppss, args.PDR_ADDRS, args.ST, args.END, args.CSVDIR)


@enforce_types
def do_get_system_info():
    parser = GetSystemInfoArgParser("Get system info", "get_system_info")
    args = parser.parse_args()
    print_args(args)

    ppss = PPSS(yaml_filename=args.YAML_FILE, network=args.NETWORK)
    
    # get all feeds and yield system stats
    addresses = get_all_contract_ids_by_owner(
        owner_address=ppss.web3_pp.owner_addrs,
        # network=ppss.web3_pp.network,
        network="mainnet",
    )

    get_system_info_main(ppss, [addresses[0]], args.ST, args.END)


@enforce_types
def do_check_network():
    parser = CheckNetworkArgParser("Check network", "check_network")
    args = parser.parse_args()
    print_args(args)

    ppss = PPSS(yaml_filename=args.YAML_FILE, network=args.NETWORK)
    check_network_main(ppss, args.LOOKBACK_HOURS)


@enforce_types
def do_trueval(testing=False):
    parser = TruevalArgParser("Run trueval bot", "trueval")
    args = parser.parse_args()
    print_args(args)

    ppss = PPSS(yaml_filename=args.YAML_FILE, network=args.NETWORK)

    approach = args.APPROACH
    if approach == 1:
        agent = TruevalAgentSingle(ppss, get_trueval)
    elif approach == 2:
        predictoor_batcher_addr = get_address(ppss.web3_pp, "PredictoorHelper")
        agent = TruevalAgentBatch(ppss, get_trueval, predictoor_batcher_addr)
    else:
        raise ValueError(f"Unknown trueval approach {approach}")

    agent.run(testing)


# @enforce_types
def do_dfbuyer():
    parser = DfbuyerArgParser("Run dfbuyer bot", "dfbuyer")
    args = parser.parse_args()
    print_args(args)

    ppss = PPSS(yaml_filename=args.YAML_FILE, network=args.NETWORK)
    agent = DFBuyerAgent(ppss)
    agent.run()


@enforce_types
def do_publisher():
    parser = PublisherArgParser("Publish feeds", "publisher")
    args = parser.parse_args()
    print_args(args)

    ppss = PPSS(yaml_filename=args.YAML_FILE, network=args.NETWORK)
    publish_assets(ppss.web3_pp, ppss.publisher_ss)


@enforce_types
def do_topup():
    parser = CheckNetworkArgParser(
        "Topup OCEAN and ROSE in dfbuyer, trueval, ..", "topup"
    )
    args = parser.parse_args()
    print_args(args)

    ppss = PPSS(yaml_filename=args.YAML_FILE, network=args.NETWORK)
    topup_main(ppss)
