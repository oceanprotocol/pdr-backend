from unittest.mock import patch

from enforce_typing import enforce_types

from pdr_backend.ppss.web3_pp import mock_web3_pp
from pdr_backend.util.web3_accounts import (
    create_accounts,
    fund_accounts,
    print_balances,
)
from pdr_backend.util.currency_types import Eth


@enforce_types
@patch("eth_account.Account.create")
def test_create_accounts(mock_create):
    create_accounts(2)

    # assert mock_create was called twice
    assert mock_create.call_count == 2


@enforce_types
@patch("pdr_backend.ppss.web3_pp.Token")
@patch("pdr_backend.ppss.web3_pp.NativeToken")
@patch("pdr_backend.ppss.web3_pp.Web3PP.get_address")
def test_print_balances(mock_get_address, mock_native_token, mock_token):
    web3_pp = mock_web3_pp("development")

    # Create Mock instances for NativeToken and Token
    ROSE = mock_native_token.return_value
    OCEAN = mock_token.return_value

    # Set the return values for balanceOf methods
    ROSE.balanceOf.return_value = Eth(2).to_wei()
    OCEAN.balanceOf.return_value = Eth(1).to_wei()

    # Set the return value for get_address
    mock_get_address.return_value = "0xOCEAN"

    print_balances("0x123", web3_pp)

    # Assert methods are returning right values
    assert mock_get_address(web3_pp, "Ocean") == "0xOCEAN"
    assert ROSE.balanceOf(mock_get_address) == Eth(2).to_wei()
    assert OCEAN.balanceOf(mock_get_address) == Eth(1).to_wei()

    # Assert methods were called the right amount of times
    assert ROSE.balanceOf.call_count == 2
    assert OCEAN.balanceOf.call_count == 2
    assert mock_get_address.call_count == 2


@enforce_types
@patch("eth_account.Account.from_key")
@patch("pdr_backend.ppss.web3_pp.Token")
@patch("pdr_backend.ppss.web3_pp.NativeToken")
@patch("pdr_backend.ppss.web3_pp.Web3PP.get_address")
def test_fund_accounts(
    mock_get_address, mock_native_token, mock_token, mock_account_from_key
):
    web3_pp = mock_web3_pp("sapphire-mainnet")

    # Create Mock instances for NativeToken and Token
    native_token_instance = mock_native_token.return_value
    token_instance = mock_token.return_value

    # Set the return value for get_address
    mock_get_address.return_value = "0xOCEAN"

    # Create Mock instances for Account
    account_instance = mock_account_from_key.return_value

    # Set the return value for Account.from_key
    mock_account_from_key.return_value = account_instance

    # Set the return value for Account.from_key
    account_instance.address = "0x123"

    # Set the return value for token.transfer
    token_instance.transfer.return_value = True

    # Test both Native & Token transfers
    fund_accounts(Eth(1.0), ["0x123", "0x124"], web3_pp, False)
    fund_accounts(Eth(3.5), ["0x125", "0x126", "0x127"], web3_pp, True)

    # Assert internals were called twice, but get_address is only called once
    assert mock_account_from_key.call_count == 2
    assert mock_get_address.call_count == 1

    # Assert 3 native token vs. 2 token transfers
    assert token_instance.transfer.call_count == 2
    assert native_token_instance.transfer.call_count == 3
