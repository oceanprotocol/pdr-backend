import sys

from enforce_typing import enforce_types

from pdr_backend.ppss.ppss import PPSS
from pdr_backend.sim.sim_engine import SimEngine
from pdr_backend.predictoor.approach1.predictoor_agent1 import PredictoorAgent1
from pdr_backend.predictoor.approach3.predictoor_agent3 import PredictoorAgent3
from pdr_backend.predictoor.payout import do_payout, do_rose_payout
from pdr_backend.trader.approach1.trader_agent1 import TraderAgent1
from pdr_backend.trader.approach2.trader_agent2 import TraderAgent2
from pdr_backend.trueval.trueval_agent_base import get_trueval
from pdr_backend.trueval.trueval_agent_batch import TruevalAgentBatch
from pdr_backend.trueval.trueval_agent_single import TruevalAgentSingle
from pdr_backend.util.cli_arguments import (
    do_help_long,
    DfbuyerArgParser,
    print_args,
    PredictoorArgParser,
    PublisherArgParser,
    SimArgParser,
    TraderArgParser,
    TruevalArgParser,
)
from pdr_backend.util.contract import get_address


@enforce_types
def _do_main():
    if len(sys.argv) <= 1 or sys.argv[1] == "help":
        do_help_long(0)

    func_name = f"do_{sys.argv[1]}"
    func = globals().get(func_name)
    if func is None:
        do_help_long(1)

    func()


@enforce_types
def do_sim():
    parser = SimArgParser("Run simulation", "sim")
    args = parser.parse_args()
    print_args(args)

    dummy_network = "barge-pytest"
    ppss = PPSS(dummy_network, args.YAML_FILE)
    sim_engine = SimEngine(ppss)
    sim_engine.run()


@enforce_types
def do_predictoor():
    parser = PredictoorArgParser("Run a predictoor bot", "predictoor")
    args = parser.parse_args()
    print_args(args)

    ppss = PPSS(args.NETWORK, args.YAML_FILE)

    approach = args.APPROACH
    if approach == 1:
        agent = PredictoorAgent1(ppss)
        agent.run()

    elif approach == 2:
        # must import here, otherwise it wants MODELDIR envvar
        from pdr_backend.predictoor.approach2.main2 import (  # pylint: disable=import-outside-toplevel
            do_main2,
        )

        do_main2()

    elif approach == 3:
        agent = PredictoorAgent3(ppss)
        agent.run()

    else:
        raise ValueError(f"Unknown predictoor approach {approach}")


@enforce_types
def do_trader():
    parser = TraderArgParser("Run a trader bot", "trader")
    args = parser.parse_args()
    print_args(args)

    ppss = PPSS(args.NETWORK, args.YAML_FILE)
    approach = args.APPROACH

    if approach == 1:
        agent = TraderAgent1(ppss)
    elif approach == 2:
        agent = TraderAgent2(ppss)
    else:
        raise ValueError(f"Unknown trader approach {approach}")

    agent.run()


@enforce_types
def do_claim_OCEAN():
    do_payout()


@enforce_types
def do_claim_ROSE():
    do_rose_payout()


@enforce_types
def do_trueval(testing=False):
    parser = TruevalArgParser("Run trueval bot", "trueval")
    args = parser.parse_args()
    print_args(args)

    ppss = PPSS(args.YAML_FILE)
    approach = args.APPROACH

    if approach == 1:
        agent = TruevalAgentSingle(ppss, get_trueval)
    elif approach == 2:
        predictoor_batcher_addr = get_address(
            ppss.web3_pp.web3_config.w3.eth.chain_id, "PredictoorHelper"
        )
        agent = TruevalAgentBatch(ppss, get_trueval, predictoor_batcher_addr)
    else:
        raise ValueError(f"Unknown trueval approach {approach}")

    agent.run(testing)



@enforce_types
def do_dfbuyer():
    parser = DfbuyerArgParser("Run dfbuyer bot", "dfbuyer")
    args = parser.parse_args()
    print_args(args)

    ppss = PPSS(args.NETWORK, args.YAML_FILE)  # pylint: disable=unused-variable
    raise AssertionError("FIXME")


@enforce_types
def do_publisher():
    parser = PublisherArgParser("Publish feeds", "publisher")
    args = parser.parse_args()
    print_args(args)

    ppss = PPSS(args.NETWORK, args.YAML_FILE)  # pylint: disable=unused-variable
    raise AssertionError("FIXME")
