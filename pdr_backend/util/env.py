import logging
import sys
from os import getenv
from typing import Union

from enforce_typing import enforce_types

logger = logging.getLogger(__name__)


@enforce_types
def getenv_or_exit(envvar_name: str) -> Union[None, str]:
    value = getenv(envvar_name)
    if value is None:
        logger.error(f"You must set {envvar_name} environment variable")
        sys.exit(1)
    return value
