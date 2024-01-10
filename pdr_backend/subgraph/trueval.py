from typing import Union

from enforce_typing import enforce_types


@enforce_types
class Trueval:
    # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        ID: str,
        timestamp: int,
        token: str,
        trueval: Union[bool, None],
        slot: int,  # slot/epoch timestamp
    ) -> None:
        self.ID = ID
        self.trueval = trueval
        self.timestamp = timestamp
        self.token = token
        self.slot = slot
