from enforce_typing import enforce_types

from pdr_backend.subgraph.trueval import Trueval, mock_truevals


@enforce_types
def test_subscriptions():
    truevals = mock_truevals()

    assert len(truevals) == 6
    assert isinstance(truevals[0], Trueval)
    assert isinstance(truevals[1], Trueval)
    assert truevals[0].ID == "0x8165caab33131a4ddbf7dc79f0a8a4920b0b2553-1696838400"
    assert truevals[1].ID == "0x8165caab33131a4ddbf7dc79f0a8a4920b0b2553-1696838100"
