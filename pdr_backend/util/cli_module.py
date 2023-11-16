import argparse
import os
import sys

from enforce_typing import enforce_types

from pdr_backend.data_eng.ppss import PPSS
from pdr_backend.sim.sim_engine import SimEngine
from pdr_backend.util.cli_arguments import (
    do_help_long,
    SimArgParser,
    PredictoorArgParser,
    TraderArgParser,
    ClaimArgParser,
    TruevalArgParser,
    DfbuyerArgParser,
    PublisherArgParser,
)


@enforce_types
def do_add_sim():
    parser = SimArgParser("Run simulation", "sim")

    arguments = parser.parse_args()
    print_arguments(arguments)

    #do work
    ppss = PPSS(arguments.YAML_FILENAME)
    print(ppss)
    sim_engine = SimEngine(ppss)
    sim_engine.run()

    
@enforce_types
def do_add_predictoor():
    parser = PredictoorArgParser("Run a predictoor bot", "predictoor")

    arguments = parser.parse_args()
    print_arguments(arguments)

    #do work
    ppss = PPSS(arguments.YAML_FILENAME)
    print(ppss)
    raise AssertionError("FIXME")


@enforce_types
def do_add_trader():
    parser = TraderArgParser("Run a trader bot", "trader")

    arguments = parser.parse_args()
    print_arguments(arguments)

    #do work
    ppss = PPSS(arguments.YAML_FILENAME)
    print(ppss)
    raise AssertionError("FIXME")


@enforce_types
def do_add_claim():
    parser = ClaimArgParser("Claim payout", "claim")

    arguments = parser.parse_args()
    print_arguments(arguments)

    #do work
    raise AssertionError("FIXME")


@enforce_types
def do_add_trueval():
    parser = TruevalArgParser("Run trueval bot", "trueval")

    arguments = parser.parse_args()
    print_arguments(arguments)

    #do work
    raise AssertionError("FIXME")


@enforce_types
def do_add_dfbuyer():
    parser = DfBuyerArgParser("Run dfbuyer bot", "dfbuyer")

    arguments = parser.parse_args()
    print_arguments(arguments)

    #do work
    raise AssertionError("FIXME")


@enforce_types
def do_add_publisher():
    parser = PublisherArgParser("Publish feeds", "publisher")

    arguments = parser.parse_args()
    print_arguments(arguments)

    #do work
    raise AssertionError("FIXME")


@enforce_types
def _do_main():
    if len(sys.argv) <= 1 or sys.argv[1] == "help":
        do_help_long(0)

    func_name = f"do_{sys.argv[1]}"
    func = globals().get(func_name)
    if func is None:
        do_help_long(1)

    func()
