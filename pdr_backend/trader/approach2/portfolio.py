from enum import Enum
import logging
from typing import Dict, List, Optional
from enforce_typing import enforce_types
from pdr_backend.util.time_types import UnixTimeMilliseconds

logger = logging.getLogger("portfolio")


class OrderState(Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class Order:
    """
    @description
        Base class for handling orders from different exchanges
        Exchanges return a blob as a trade, there is no solution for this in CCXT
    """

    def __init__(self, order: Dict):
        self.order = order

    def __str__(self):
        return f"<{self.order}, {self.__class__}>"

    @property
    def id(self):
        return None

    @property
    def amount(self):
        return None

    @property
    def timestamp(self) -> Optional[UnixTimeMilliseconds]:
        return None


class MexcOrder(Order):
    def __init__(self, order: Dict):  # pylint: disable=useless-parent-delegation
        super().__init__(order)

    @property
    def id(self):
        return self.order["id"]

    @property
    def amount(self):
        return self.order["info"]["origQty"]

    @property
    def timestamp(self) -> UnixTimeMilliseconds:
        return UnixTimeMilliseconds(self.order["timestamp"])


@enforce_types
def create_order(order: Dict, exchange_str: str) -> Order:
    return MexcOrder(order) if exchange_str == "mexc" else Order(order)


class Position:
    """
    @description
        Has an open and and a close order minimum
    """

    def __init__(self, order: Order):
        self.open_order: Order = order
        self.close_order: Optional[Order] = None
        self.state: OrderState = OrderState.OPEN

        logger.info("[Opening Order] %s", self.open_order)

    def __str__(self):
        return f"<{self.open_order}, {self.close_order}, {self.__class__}>"

    def close(self, order: Order):
        self.close_order = order
        self.state = OrderState.CLOSED

        # calculate costs, profits, and PNL
        logger.info("[Opening Order]: %s", self.open_order)
        logger.info("[Closing Order]: %s", self.close_order)


class Sheet:
    """
    @description
        Holds N positions for an asset, specified by an addr (key)
    """

    def __init__(self, addr: str):
        self.asset: str = addr
        self.open_positions: List[Position] = []
        self.closed_positions: List[Position] = []

    def open_position(self, open_order: Order) -> Position:
        position = Position(open_order)
        self.open_positions.append(position)
        logger.info("[Position added to Sheet]")
        return position

    def close_position(self, close_order: Order) -> Optional[Position]:
        position = self.open_positions.pop() if self.open_positions else None

        if not position:
            return None

        position.close(close_order)
        self.closed_positions.append(position)
        logger.info("[Position closed in Sheet]")
        return position


class Portfolio:
    """
    @description
        Handles assets across a variety of exchanges, and instruments.
        They map 1:1 to the prediction feeds that we trade against
    """

    def __init__(self, feeds: List[str]):
        self.sheets: Dict[str, Sheet] = {addr: Sheet(addr) for addr in feeds}

    def get_sheet(self, addr: str) -> Optional[Sheet]:
        return self.sheets.get(addr, None)

    def open_position(self, addr: str, order: Order) -> Optional[Position]:
        sheet = self.get_sheet(addr)
        return sheet.open_position(order) if sheet else None

    def close_position(self, addr: str, order: Order) -> Optional[Position]:
        sheet = self.get_sheet(addr)
        return sheet.close_position(order) if sheet else None
