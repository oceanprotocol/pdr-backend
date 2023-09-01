import sys

from enforce_typing import enforce_types

HELP = """Predictoor runner.

Usage: python pdr_backend/predictoor/main.py APPROACH

       where APPROACH=1 does random predictions
             APPROACH=2 uses a model to predict. Needs MODELDIR specified.
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
    if arg1 == "1":
        from pdr_backend.predictoor.approach1.main1 import (  # pylint: disable=import-outside-toplevel,line-too-long
            do_main1,
        )

        do_main1()

    elif arg1 == "2":
        from pdr_backend.predictoor.approach2.main2 import (  # pylint: disable=import-outside-toplevel,line-too-long
            do_main2,
        )

        do_main2()

    elif arg1 == "help":
        do_help()

    else:
        do_help()


if __name__ == "__main__":
    do_main()
