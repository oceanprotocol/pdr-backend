from enforce_typing import enforce_types

from pdr_backend.exchange.mock_order import MockOrder


@enforce_types
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
