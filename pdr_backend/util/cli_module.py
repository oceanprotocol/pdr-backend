import argparse
import importlib
import os
import sys

from enforce_typing import enforce_types

from pdr_backend.data_eng.ppss import PPSS
from pdr_backend.sim.sim_engine import SimEngine
from pdr_backend.predictoor.approach1.predictoor_agent1 import PredictoorAgent1
from pdr_backend.predictoor.approach3.predictoor_agent3 import PredictoorAgent3
from pdr_backend.predictoor.payout import do_payout, do_rose_payout
from pdr_backend.trader.trader_agent import TraderAgent
from pdr_backend.trader.trader_config import TraderConfig
from pdr_backend.util.cli_arguments import (
    do_help_long,
    print_args,
    SimArgParser,
    PredictoorArgParser,
    TraderArgParser,
    TruevalArgParser,
    DfbuyerArgParser,
    PublisherArgParser,
)


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

    ppss = PPSS(args.YAML_FILE)
    sim_engine = SimEngine(ppss)
    sim_engine.run()

    
@enforce_types
def do_predictoor():
    parser = PredictoorArgParser("Run a predictoor bot", "predictoor")
    args = parser.parse_args()
    print_args(args)

    ppss = PPSS(args.YAML_FILE)

    approach = args.APPROACH
    if approach == 1:
        agent = PredictoorAgent1(config, ppss)
        agent.run()
                
    elif approach == 2:
        # must import here, otherwise it wants MODELDIR envvar
        from pdr_backend.predictoor.approach2.main2 import do_main2x
        do_main2()
        
    elif approach == 3:
        agent = PredictoorAgent3(config, ppss)
        agent.run()

    else:
        raise ValueError(f"Unknown predictoor approach {appr}")


@enforce_types
def do_trader():
    parser = TraderArgParser("Run a trader bot", "trader")
    args = parser.parse_args()
    print_args(args)

    ## TO DO: use this
    # ppss = PPSS(args.YAML_FILE)

    ## TO DO: use args.APPROACH
    
    config = TraderConfig()
    t = TraderAgent(config)
    t.run(testing)

    
@enforce_types
def do_claim_OCEAN():
    do_payout()

    
@enforce_types
def do_claim_ROSE():
    do_rose_payout()

    
@enforce_types
def do_trueval():
    parser = TruevalArgParser("Run trueval bot", "trueval")
    args = parser.parse_args()
    print_args(args)

    ppss = PPSS(args.YAML_FILE)
    raise AssertionError("FIXME")


@enforce_types
def do_dfbuyer():
    parser = DfBuyerArgParser("Run dfbuyer bot", "dfbuyer")
    args = parser.parse_args()
    print_args(args)

    ppss = PPSS(args.YAML_FILE)
    raise AssertionError("FIXME")


@enforce_types
def do_publisher():
    parser = PublisherArgParser("Publish feeds", "publisher")
    args = parser.parse_args()
    print_args(args)

    ppss = PPSS(args.YAML_FILE)
    raise AssertionError("FIXME")

