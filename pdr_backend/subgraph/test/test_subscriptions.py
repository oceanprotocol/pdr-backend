from enforce_typing import enforce_types

from pdr_backend.subgraph.subscription import Subscription, mock_subscriptions


@enforce_types
def test_subscriptions():
    subscriptions = mock_subscriptions()

    assert len(subscriptions) == 8
    assert isinstance(subscriptions[0], Subscription)
    assert isinstance(subscriptions[1], Subscription)
    assert (
        subscriptions[0].ID
        == "ETH/USDT-0x01d3285e0e3b83a4c029142477c0573c3be5317ff68223703696093b27809592-98"
    )
    assert (
        subscriptions[1].ID
        == "BTC/USDT-0x01d3285e0e3b83a4c029142477c0573c3be5317ff68223703696093b27809593-99"
    )
