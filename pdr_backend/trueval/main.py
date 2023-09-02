import sys

from enforce_typing import enforce_types

from pdr_backend.trueval.trueval_agent_base import get_trueval
from pdr_backend.trueval.trueval_agent_batch import TruevalAgentBatch
from pdr_backend.trueval.trueval_agent_single import TruevalAgentSingle
from pdr_backend.trueval.trueval_config import TruevalConfig
from pdr_backend.util.contract import get_address


HELP = """Trueval runner.

Usage: python pdr_backend/trueval/main.py APPROACH

       where APPROACH=1 submits truevals one by one
             APPROACH=2 submits truevals in a batch
"""


def do_help():
    print(HELP)
    sys.exit()


@enforce_types
def main(testing=False):
    if len(sys.argv) <= 1:
        do_help()
    arg1 = sys.argv[1]
    config = TruevalConfig()

    if arg1 == "1":
        t = TruevalAgentSingle(config, get_trueval)
        t.run(testing)

    elif arg1 == "2":
        predictoor_batcher_addr = get_address(
            config.web3_config.w3.eth.chain_id, "PredictoorHelper"
        )
        t = TruevalAgentBatch(config, get_trueval, predictoor_batcher_addr)
        t.run(testing)

    elif arg1 == "help":
        do_help()
    else:
        do_help()


if __name__ == "__main__":
    main()
