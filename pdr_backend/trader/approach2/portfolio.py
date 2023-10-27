from pdr_backend.models.feed import Feed
from typing import Dict, List
from enum import Enum
import ccxt


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
    def timestamp(self):
        return None


class MEXCOrder(Order):
    def __init__(self, order: Dict):
        super().__init__(order)

    @property
    def id(self):
        return self.order["id"]

    @property
    def amount(self):
        return self.order["info"]["origQty"]

    @property
    def timestamp(self):
        return self.order["timestamp"]


def create_order(order: Dict, exchange: ccxt.Exchange):
    if exchange in ("mexc", "mexc3"):
        return MEXCOrder(order)
    return Order(order)


class Position:
    """
    @description
        Has an open and and a close order minimum
        TODO - Support many buy/sell orders, balance, etc...
    """

    def __init__(self, order: Order):
        # TODO - Have N open_orders, have N close_orders
        # TODO - Move from __init__(order) to open(order)
        self.open_order = order
        self.close_order = None
        self.state: OrderState = OrderState.OPEN

        print(f"     [Opening Order] {self.open_order}")

    def __str__(self):
        return f"<{self.open_order}, {self.close_order}, {self.__class__}>"

    # TODO - Only callable by portfolio
    def close(self, order: Order):
        self.close_order = order
        self.state = OrderState.CLOSED

        # calculate costs, profits, and PNL
        print(f"     [Opening Order]: {self.open_order}")
        print(f"     [Closing Order] {self.close_order}")


class Sheet:
    """
    @description
        Holds N positions for an asset, specified by an addr (key)
    """

    def __init__(self, addr):
        self.asset = addr
        self.open_positions: List[Position] = []
        self.closed_positions: List[Position] = []

    def open_position(self, open_order: Order) -> Position:
        position = Position(open_order)
        self.open_positions.append(position)
        print(f"     [Position added to Sheet]")
        return position

    def close_position(self, close_order: Order) -> Position:
        position = self.open_positions.pop()
        if position:
            position.close(close_order)
            self.closed_positions.append(position)
            print(f"     [Position closed in Sheet]")
            return position
        return None


class Portfolio:
    """
    @description
        Handles assets across a variety of exchanges, and instruments.
        They map 1:1 to the prediction feeds that we trade against
    """

    def __init__(self, feeds: List[Feed]):
        self.sheets: Dict[str, Sheet] = {addr: Sheet(addr) for addr in feeds}

    def get_sheet(self, addr: str) -> Sheet:
        return self.sheets.get(addr, None)

    def open_position(self, addr: str, order: Order) -> Position:
        sheet = self.get_sheet(addr)
        if sheet:
            return sheet.open_position(order)

    def close_position(self, addr: str, order: Order) -> Position:
        sheet = self.get_sheet(addr)
        if sheet:
            return sheet.close_position(order)
