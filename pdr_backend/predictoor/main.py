import importlib
import sys

from enforce_typing import enforce_types

HELP = """Predictoor runner.

Usage: python pdr_backend/predictoor/main.py APPROACH

       where APPROACH=1 - does random predictions
             APPROACH=2 - uses a model to predict. Needs MODELDIR specified.
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
    if arg1 in ["1", "2"]:
        agent_class = importlib.import_module(
            f"pdr_backend.predictoor.approach{arg1}.predictoor_agent{arg1}"
        )
        agent_class = getattr(agent_class, f"PredictoorAgent{arg1}")
        config = agent_class.predictoor_config_class()
        agent = agent_class(config)
        agent.run()
    elif arg1 == "payout":
        # pylint: disable=import-outside-toplevel
        from pdr_backend.predictoor.payout import do_payout

        do_payout()

    elif arg1 == "help":
        do_help()

    else:
        do_help()


if __name__ == "__main__":
    do_main()
