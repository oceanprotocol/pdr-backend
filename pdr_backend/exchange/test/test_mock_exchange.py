import ccxt
from enforce_typing import enforce_types

from pdr_backend.exchange.mock_exchange import MockExchange
from pdr_backend.exchange.mock_order import MockOrder


@enforce_types
def test_mock_exchange():
    mock_exchange = MockExchange()
    assert str(mock_exchange) == "mocked exchange"
    assert isinstance(mock_exchange, ccxt.Exchange)
    assert isinstance(mock_exchange.create_market_buy_order("BTC/USDT", 0.1), MockOrder)
    assert isinstance(
        mock_exchange.create_market_sell_order("BTC/USDT", 0.1), MockOrder
    )
