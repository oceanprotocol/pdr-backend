import argparse
import os
import sys

from enforce_typing import enforce_types

from pdr_backend.data_eng.ppss import PPSS
from pdr_backend.sim.sim_engine import SimEngine
from pdr_backend.util.cli_arguments import (
    do_help_long,
    print_args,
    SimArgParser,
    PredictoorArgParser,
    TraderArgParser,
    ClaimArgParser,
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

    #do work
    ppss = PPSS(args.YAML_FILE)
    print(ppss)
    sim_engine = SimEngine(ppss)
    sim_engine.run()

    
@enforce_types
def do_predictoor():
    parser = PredictoorArgParser("Run a predictoor bot", "predictoor")
    args = parser.parse_args()
    print_args(args)

    #do work
    ppss = PPSS(args.YAML_FILE)
    print(ppss)
    raise AssertionError("FIXME")


@enforce_types
def do_trader():
    parser = TraderArgParser("Run a trader bot", "trader")
    args = parser.parse_args()
    print_args(args)

    #do work
    ppss = PPSS(args.YAML_FILE)
    print(ppss)
    raise AssertionError("FIXME")


@enforce_types
def do_claim():
    parser = ClaimArgParser("Claim payout", "claim")
    args = parser.parse_args()
    print_args(args)

    #do work
    raise AssertionError("FIXME")


@enforce_types
def do_trueval():
    parser = TruevalArgParser("Run trueval bot", "trueval")
    args = parser.parse_args()
    print_args(args)

    #do work
    ppss = PPSS(args.YAML_FILE)
    print(ppss)
    raise AssertionError("FIXME")


@enforce_types
def do_dfbuyer():
    parser = DfBuyerArgParser("Run dfbuyer bot", "dfbuyer")
    args = parser.parse_args()
    print_args(args)

    #do work
    ppss = PPSS(args.YAML_FILE)
    print(ppss)
    raise AssertionError("FIXME")


@enforce_types
def do_publisher():
    parser = PublisherArgParser("Publish feeds", "publisher")
    args = parser.parse_args()
    print_args(args)

    #do work
    ppss = PPSS(args.YAML_FILE)
    print(ppss)
    raise AssertionError("FIXME")

