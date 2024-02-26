from typing import Union
from enforce_typing import enforce_types


@enforce_types
class Eth:
    def __init__(self, amt_eth: Union[int, float]):
        # TODO: validation
        if False:
            raise ValueError("Invalid value in eth {amt_eth}")

        self.amt_eth = amt_eth

    def to_wei(self) -> "Wei":
        return Wei(int(self.amt_eth * 1e18))

    def __str__(self) -> str:
        return f"{self.amt_eth} eth"

    def __repr__(self) -> str:
        return self.__str__()

    def __float__(self) -> float:
        return self.amt_eth

    def __lt__(self, other) -> bool:
        if isinstance(other, Eth):
            return self.amt_eth < other.amt_eth

        return self.amt_eth < other

    def __gt__(self, other) -> bool:
        if isinstance(other, Eth):
            return self.amt_eth > other.amt_eth

        return self.amt_eth > other

    def __sub__(self, other) -> "Eth":
        if isinstance(other, Eth):
            return Eth(self.amt_eth - other.amt_eth)

        return Eth(self.amt_eth - other)

    def __eq__(self, other) -> bool:
        if isinstance(other, Eth):
            return self.amt_eth == other.amt_eth

        return self.amt_eth == other


@enforce_types
class Wei:
    def __init__(self, amt_wei: Union[int, float]):
        # TODO: validation
        if False:
            raise ValueError("Invalid value in wei {amt_wei}")

        self.amt_wei = amt_wei

    # old from_wei
    def to_eth(self) -> Eth:
        return Eth(float(self.amt_wei / 1e18))

    def str_with_wei(self) -> str:
        return f"{self.to_eth().amt_eth} ({self.amt_wei} wei)"

    def __str__(self) -> str:
        return f"{self.amt_wei} wei"

    def __repr__(self) -> str:
        return self.__str__()

    def __lt__(self, other) -> bool:
        if isinstance(other, Wei):
            return self.amt_wei < other.amt_wei

        return self.amt_wei < other

    def __gt__(self, other) -> bool:
        if isinstance(other, Wei):
            return self.amt_wei > other.amt_wei

        return self.amt_wei > other

    def __le__(self, other) -> bool:
        if isinstance(other, Wei):
            return self.amt_wei <= other.amt_wei

        return self.amt_wei <= other

    def __eq__(self, other) -> bool:
        if isinstance(other, Wei):
            return self.amt_wei == other.amt_wei

        return self.amt_wei == other

    def __add__(self, other) -> "Wei":
        if isinstance(other, Wei):
            return Wei(self.amt_wei + other.amt_wei)

        return Wei(self.amt_wei + other)

    def __sub__(self, other) -> "Wei":
        if isinstance(other, Wei):
            return Wei(self.amt_wei - other.amt_wei)

        return Wei(self.amt_wei - other)
