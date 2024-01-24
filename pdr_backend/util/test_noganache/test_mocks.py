import ccxt

from pdr_backend.util.mocks import MockExchange, MockOrder


def test_mock_order():
    mock_order = MockOrder(
        {
            "order_type": "buy",
            "amount": "0.1",
            "pair_str": "BTC/USDT",
        }
    )
    assert str(mock_order) == "mocked order: 0.1 BTC/USDT"
    assert isinstance(mock_order, dict)


def test_mock_exchange():
    mock_exchange = MockExchange()
    assert str(mock_exchange) == "mocked exchange"
    assert isinstance(mock_exchange, ccxt.Exchange)
    assert isinstance(mock_exchange.create_market_buy_order("BTC/USDT", 0.1), MockOrder)
    assert isinstance(
        mock_exchange.create_market_sell_order("BTC/USDT", 0.1), MockOrder
    )
