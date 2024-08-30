#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import time
from unittest.mock import patch

from enforce_typing import enforce_types

from pdr_backend.contract.token import Token
from pdr_backend.util.currency_types import Wei


@enforce_types
def test_token(web3_pp, web3_config):
    token_address = web3_pp.OCEAN_address
    token = Token(web3_pp, token_address)

    accounts = web3_config.w3.eth.accounts
    owner_addr = web3_config.owner
    alice = accounts[1]

    call_params = web3_pp.tx_call_params()
    unsigned = token.contract_instance.functions.mint(
        owner_addr, 1000000000
    ).build_transaction(call_params)
    unsigned["nonce"] = web3_config.w3.eth.get_transaction_count(call_params["from"])
    signed = web3_config.w3.eth.account.sign_transaction(
        unsigned, private_key=web3_pp.private_key
    )
    web3_config.w3.eth.send_raw_transaction(signed.raw_transaction)

    allowance_start = token.allowance(owner_addr, alice)
    token.approve(alice, allowance_start + 100, True)
    time.sleep(1)
    allowance_end = token.allowance(owner_addr, alice)
    assert allowance_end - allowance_start == Wei(100)

    balance_start = token.balanceOf(alice)
    token.transfer(alice, Wei(100), owner_addr)
    balance_end = token.balanceOf(alice)
    assert balance_end - balance_start == Wei(100)


@enforce_types
def test_native_token(web3_pp):
    token = web3_pp.NativeToken
    assert token.w3

    owner = web3_pp.web3_config.owner
    assert token.balanceOf(owner)

    with patch("web3.eth.Eth.send_transaction") as mock:
        token.transfer(owner, Wei(100), "0x123", False)
        assert mock.called
