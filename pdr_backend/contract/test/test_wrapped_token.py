#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from unittest.mock import Mock, patch

from enforce_typing import enforce_types

from pdr_backend.contract.wrapped_token import WrappedToken
from pdr_backend.util.currency_types import Wei


@enforce_types
def test_native_token(web3_pp):
    token_address = web3_pp.get_address("Ocean")
    mock_wrapped_contract = Mock()
    mock_transaction = Mock()
    mock_transaction.transact.return_value = "mock_tx"
    mock_wrapped_contract.functions.withdraw.return_value = mock_transaction

    with patch("web3.eth.Eth.contract") as mock:
        mock.return_value = mock_wrapped_contract
        token = WrappedToken(web3_pp, token_address)

    assert token.withdraw(Wei(100), False) == "mock_tx"
