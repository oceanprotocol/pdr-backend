from enforce_typing import enforce_types

from pdr_backend.lake.subscription import Subscription, mock_subscriptions


@enforce_types
def test_subscriptions():
    subscriptions = mock_subscriptions()

    assert len(subscriptions) == 9
    assert isinstance(subscriptions[0], Subscription)
    assert isinstance(subscriptions[1], Subscription)
    assert (
        subscriptions[0].ID
        == """0x18f54cc21b7a2fdd011bea06bba7801b280e3151-
        0xe4599d8d1a02330fbc3a2a8fb4950f6d5a44d2e85fe750438246f535b47eda35-98"""
    )
    assert (
        subscriptions[1].ID
        == """0x18f54cc21b7a2fdd011bea06bba7801b280e3151-
        0xe4599d8d1a02330fbc3a2a8fb4950f6d5a44d2e85fe750438246f535b47eda35-98"""
    )
