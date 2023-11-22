from os import getenv
import sys
from typing import Union

from enforce_typing import enforce_types


@enforce_types
def getenv_or_exit(envvar_name: str) -> Union[None, str]:
    value = getenv(envvar_name)
    if value is None:
        print(f"You must set {envvar_name} environment variable")
        sys.exit(1)
    return value
