from unittest.mock import patch

import polars as pl
from pdr_backend.lake.table_pdr_truevals import get_pdr_truevals_df
from pdr_backend.subgraph.trueval import mock_truevals

# ====================================================================
pdr_subscriptions_record = "pdr_subscriptions"


@patch("pdr_backend.lake.table_pdr_truevals.fetch_truevals")
def test_get_pdr_truevals_df(mock_fetch_truevals):
    mock_fetch_truevals.return_value = mock_truevals()
    trueval_def = get_pdr_truevals_df(
        "sapphire-testnet",
        1696879672,
        1696885995,
        {
            "name": "Sapphire",
            "contract_list": ["0x18f54cc21b7a2fdd011bea06bba7801b280e3151"],
        },
    )

    # check if return type is a Polar Data Frame
    assert isinstance(trueval_def, pl.DataFrame)

    # check the number of objects in Data Frame
    assert trueval_def.shape[0] == 6


@patch("pdr_backend.lake.table_pdr_truevals.fetch_truevals")
def test_get_pdr_truevals_no_truevals_fetched_df(mock_fetch_truevals, capfd):
    mock_fetch_truevals.return_value = []
    trueval_def = get_pdr_truevals_df(
        "sapphire-testnet",
        1696879672,
        1696885995,
        {
            "name": "Sapphire",
            "contract_list": ["0x18f54cc21b7a2fdd011bea06bba7801b280e3151"],
        },
    )

    # empty Polar Data Frame is returned
    assert trueval_def.shape[0] == 0
    assert isinstance(trueval_def, pl.DataFrame)

    # message with no truevals should be printed
    assert "No truevals to fetch." in capfd.readouterr().out
