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
        trueValue: Union[bool, None],
        slot: float,  # slot/epoch timestamp
    ) -> None:
        self.ID = ID
        self.trueValue = trueValue
        self.timestamp = timestamp
        self.token = token
        self.slot = slot
