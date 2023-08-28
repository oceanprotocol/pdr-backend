import sys

HELP = """Predictoor runner.

Usage: python pdr_backend/predictoor/main.py APPROACH

       where APPROACH=1 does random predictions
             APPROACH=2 uses a model to predict. Needs MODELDIR specified.
"""


def _do_help():
    print(HELP)
    sys.exit()


def _do_main():
    if len(sys.argv) <= 1:
        _do_help()

    approach = sys.argv[1]
    match approach:
        case "1":
            from pdr_backend.predictoor.approach1.main import (  # pylint: disable=import-outside-toplevel,line-too-long
                main,
            )

            main()

        case "2":
            from pdr_backend.predictoor.approach2.main import (  # pylint: disable=import-outside-toplevel,line-too-long
                main,
            )

            main()

        case "help":
            _do_help()

        case _:
            _do_help()


if __name__ == "__main__":
    _do_main()
