import importlib
import sys

from enforce_typing import enforce_types

HELP = """Predictoor runner.

Usage: python pdr_backend/predictoor/main.py APPROACH

       where APPROACH=1 - does random predictions
             APPROACH=2 - uses a static model to predict. Needs MODELDIR specified.
             APPROACH=3 - uses a dynamic model to predict
             APPROACH=payout - claim all unclaimed payouts.
"""


@enforce_types
def do_help():
    print(HELP)
    sys.exit()


@enforce_types
def do_main():
    if len(sys.argv) <= 1:
        do_help()

    arg1 = sys.argv[1]
    if arg1 in ["1", "3"]:  # approach1, approach3
        agent_module = importlib.import_module(
            f"pdr_backend.predictoor.approach{arg1}.predictoor_agent{arg1}"
        )
        agent_class = getattr(agent_module, f"PredictoorAgent{arg1}")
        config_class = agent_class.predictoor_config_class
        config = config_class()
        agent = agent_class(config)
        agent.run()

    elif arg1 == "2":  # approach2
        # To be integrated similar to "1"
        from pdr_backend.predictoor.approach2.main2 import (  # pylint: disable=import-outside-toplevel,line-too-long
            do_main2,
        )

        do_main2()

    elif arg1 == "payout":
        # pylint: disable=import-outside-toplevel
        from pdr_backend.predictoor.payout import do_payout

        do_payout()

    elif arg1 == "roseclaim":
        # pylint: disable=import-outside-toplevel
        from pdr_backend.predictoor.payout import do_rose_payout

        do_rose_payout()

    elif arg1 == "help":
        do_help()

    else:
        do_help()


if __name__ == "__main__":
    do_main()
