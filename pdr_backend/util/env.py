from os import getenv
import sys


def getenv_or_exit(envvar_name: str) -> str:
    value = getenv(envvar_name)
    if value is None:
        print(f"You must set {envvar_name} environment variable")
        sys.exit(1)
    return value  # type: ignore
