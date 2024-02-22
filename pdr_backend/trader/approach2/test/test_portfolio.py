from pdr_backend.trader.approach2.portfolio import (
    MexcOrder,
    Order,
    OrderState,
    Portfolio,
    Position,
    Sheet,
    create_order,
)


def test_order_classes():
    order_dict = {"id": 1, "info": {"origQty": 2}, "timestamp": 3000}

    order = Order(order_dict)
    assert order.id is None
    assert order.amount is None
    assert order.timestamp is None

    mexc_order = MexcOrder(order_dict)
    assert mexc_order.id == 1
    assert mexc_order.amount == 2
    assert mexc_order.timestamp == 3000

    assert isinstance(create_order(order_dict, "mexc"), MexcOrder)
    assert isinstance(create_order(order_dict, "other"), Order)


def test_position():
    position = Position(Order({}))
    assert position.state == OrderState.OPEN
    assert position.close_order is None

    position.close(Order({}))
    assert position.state == OrderState.CLOSED
    assert isinstance(position.close_order, Order)


def test_sheet():
    sheet = Sheet("0x123")
    assert sheet.asset == "0x123"
    assert sheet.open_positions == []
    assert sheet.closed_positions == []

    # no effect
    sheet.close_position(Order({}))
    assert sheet.open_positions == []
    assert sheet.closed_positions == []

    # open and close
    sheet.open_position(Order({}))
    assert isinstance(sheet.open_positions[0], Position)

    sheet.close_position(Order({}))
    assert isinstance(sheet.closed_positions[0], Position)
    assert sheet.open_positions == []


def test_portfolio():
    portfolio = Portfolio(["0x123", "0x456"])
    assert portfolio.sheets.keys() == {"0x123", "0x456"}

    assert portfolio.get_sheet("0x123").asset == "0x123"
    assert portfolio.get_sheet("xxxx") is None

    assert isinstance(portfolio.open_position("0x123", Order({})), Position)
    assert isinstance(portfolio.close_position("0x123", Order({})), Position)
