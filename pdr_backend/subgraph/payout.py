from enforce_typing import enforce_types

@enforce_types
class Payout:
    def __init__(
        self,
        ID: str,
        token: str,
        user: str,
        slot: int,
        timestamp: int,
        payout: float
    ) -> None:
        self.ID = ID
        self.user = user
        self.timestamp = timestamp
        self.token = token
        self.slot = slot
        self.payout = payout
