import logging
import sys
from os import getenv
from typing import Union

from enforce_typing import enforce_types

logger = logging.getLogger("env")


@enforce_types
def getenv_or_exit(envvar_name: str) -> Union[None, str]:
    value = getenv(envvar_name)
    if value is None:
        logger.error("You must set %s environment variable", envvar_name)
        sys.exit(1)
    return value
