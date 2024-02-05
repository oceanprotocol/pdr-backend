import time
from unittest.mock import patch

from enforce_typing import enforce_types

from pdr_backend.contract.token import NativeToken, Token


@enforce_types
def test_token(web3_pp, web3_config):
    token_address = web3_pp.OCEAN_address
    token = Token(web3_pp, token_address)

    accounts = web3_config.w3.eth.accounts
    owner_addr = web3_config.owner
    alice = accounts[1]

    call_params = web3_pp.tx_call_params()
    token.contract_instance.functions.mint(owner_addr, 1000000000).transact(call_params)

    allowance_start = token.allowance(owner_addr, alice)
    token.approve(alice, allowance_start + 100, True)
    time.sleep(1)
    allowance_end = token.allowance(owner_addr, alice)
    assert allowance_end - allowance_start == 100

    balance_start = token.balanceOf(alice)
    token.transfer(alice, 100, owner_addr)
    balance_end = token.balanceOf(alice)
    assert balance_end - balance_start == 100


@enforce_types
def test_native_token(web3_pp):
    token = web3_pp.NativeToken
    assert token.w3

    owner = web3_pp.web3_config.owner
    assert token.balanceOf(owner)

    with patch("web3.eth.Eth.send_transaction") as mock:
        token.transfer(owner, 100, "0x123", False)
        assert mock.called
