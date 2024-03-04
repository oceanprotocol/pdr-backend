import logging
from typing import Union
from enforce_typing import enforce_types

logger = logging.getLogger("currency_types")


@enforce_types
class EthUnit:
    def __init__(self, amount: Union[int, float]):
        self.amount = amount

    def __str__(self) -> str:
        return f"{self.amount}"

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other) -> bool:
        if isinstance(other, EthUnit):
            return self.to_wei().amount == other.to_wei().amount
        return False

    def __lt__(self, other) -> bool:
        if isinstance(other, EthUnit):
            return self.to_wei().amount < other.to_wei().amount
        return False

    def __le__(self, other) -> bool:
        if isinstance(other, EthUnit):
            return self.to_wei().amount <= other.to_wei().amount
        return False

    def __gt__(self, other) -> bool:
        if isinstance(other, EthUnit):
            return self.to_wei().amount > other.to_wei().amount
        return False

    def __ge__(self, other) -> bool:
        if isinstance(other, EthUnit):
            return self.to_wei().amount >= other.to_wei().amount
        return False

    def __add__(self, other) -> "EthUnit":
        if isinstance(other, EthUnit):
            if isinstance(self, Eth):
                return Eth(self.amt_eth + other.to_eth().amt_eth)
            elif isinstance(self, Wei):
                return Wei(self.amt_wei + other.to_wei().amt_wei)
        return NotImplemented

    def __sub__(self, other) -> "EthUnit":
        if isinstance(other, EthUnit):
            if isinstance(self, Eth):
                return Eth(self.amt_eth - other.to_eth().amt_eth)
            elif isinstance(self, Wei):
                return Wei(self.amt_wei - other.to_wei().amt_wei)
        return NotImplemented

    def __truediv__(self, other) -> "EthUnit":
        if isinstance(other, EthUnit):
            if isinstance(self, Eth) and other.amt_eth != 0:
                return Eth(self.amt_eth / other.to_eth().amt_eth)
            elif isinstance(self, Wei) and other.to_wei().amt_wei != 0:
                return Wei(self.amt_wei / other.to_wei().amt_wei)
        return NotImplemented

    def __mul__(self, other) -> "EthUnit":
        if isinstance(other, EthUnit):
            if isinstance(self, Eth):
                return Eth(self.amt_eth * other.to_eth().amt_eth)
            elif isinstance(self, Wei):
                return Wei(self.amt_wei * other.to_wei().amt_wei)
        return NotImplemented


    def __pos__(self) -> "EthUnit":
        return self.__class__(+self.amount)

    def __neg__(self) -> "EthUnit":
        return self.__class__(-self.amount)

    def __float__(self) -> float:
        return self.amount

    def to_wei(self) -> "Wei":
        """Should be overridden by subclasses"""
        raise NotImplementedError

    def to_eth(self) -> "Eth":
        """Should be overridden by subclasses"""
        raise NotImplementedError


@enforce_types
class Eth(EthUnit):
    def __init__(self, amt_eth: Union[int, float]):
        super().__init__(amt_eth)
        if amt_eth > 100_000_000_000:
            logger.warning(
                "amt_eth=%s is very large. Should it be wei instead?", amt_eth
            )

    def to_wei(self) -> "Wei":
        return Wei(int(self.amount * 1e18))

    def __str__(self) -> str:
        return f"{self.amount} eth"

    def to_eth(self) -> "Eth":
        return self

    @property
    def amt_eth(self) -> float:
        return self.amount

    @property
    def amt_wei(self) -> float:
        return self.to_wei().amt_wei

@enforce_types
class Wei(EthUnit):
    def to_eth(self) -> Eth:
        return Eth(self.amount / 1e18)

    def __str__(self) -> str:
        return f"{self.amount} wei"

    def to_wei(self) -> "Wei":
        return self

    def str_with_wei(self) -> str:
        return f"{self.to_eth().amount} eth ({self.amount} wei)"

    @property
    def amt_wei(self) -> float:
        return self.amount

    @property
    def amt_eth(self) -> float:
        return self.to_eth().amt_eth