import argparse
import os
import sys

from enforce_typing import enforce_types

from pdr_backend.sim import runsim


from pdr_backend.util.pdr_arguments import (
    do_help_long,
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
