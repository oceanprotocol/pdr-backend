from unittest.mock import Mock, patch

from enforce_typing import enforce_types
from eth_account import Account

from pdr_backend.ppss.web3_pp import del_network_override
from pdr_backend.contract.token import Token
from pdr_backend.ppss.web3_pp import mock_web3_pp
from pdr_backend.util.web3_accounts import (
    create_accounts,
    fund_accounts,
    view_accounts,
    _get_account_balances
)


@enforce_types
@patch('eth_account.Account.create')
def test_create_accounts(mock_create, monkeypatch):
    create_accounts(2)

    # assert mock_create was called twice
    assert mock_create.call_count == 2


@enforce_types
@patch('pdr_backend.util.web3_accounts.Token', autospec=True)
@patch('pdr_backend.util.web3_accounts.NativeToken', autospec=True)
@patch('pdr_backend.util.web3_accounts.get_address', autospec=True)
def test_get_account_balances(
    mock_get_address,
    mock_native_token,
    mock_token,
    monkeypatch):

    del_network_override(monkeypatch)

    web3_pp = mock_web3_pp("development")

    # Create Mock instances for NativeToken and Token
    native_token_instance = mock_native_token.return_value
    token_instance = mock_token.return_value

    # Set the return values for balanceOf methods
    native_token_instance.balanceOf.return_value = 2
    token_instance.balanceOf.return_value = 1

    # Set the return value for get_address
    mock_get_address.return_value = "0x123"
    
    native_token_balance, OCEAN_balance = _get_account_balances("0x123", web3_pp)

    # Assert the right methods were called
    assert native_token_balance == 2
    assert OCEAN_balance == 1
