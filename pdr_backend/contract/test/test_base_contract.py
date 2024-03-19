import os
from unittest.mock import Mock

import pytest
from enforce_typing import enforce_types

from pdr_backend.contract.token import Token


@pytest.fixture
def mock_send_encrypted_sapphire_tx(monkeypatch):
    mock_function = Mock(return_value=(0, "dummy_tx_hash"))
    monkeypatch.setattr("sapphirepy.wrapper.send_encrypted_sapphire_tx", mock_function)
    return mock_function


@enforce_types
def test_base_contract(web3_pp, web3_config):
    OCEAN_address = web3_pp.OCEAN_address

    # success
    Token(web3_pp, OCEAN_address)

    # catch failure
    web3_config = web3_pp.web3_config
    with pytest.raises(ValueError):
        Token(web3_config, OCEAN_address)


@enforce_types
def test_send_encrypted_tx(
    mock_send_encrypted_sapphire_tx,  # pylint: disable=redefined-outer-name
    OCEAN,
    web3_pp,
):
    OCEAN_address = web3_pp.OCEAN_address
    contract = Token(web3_pp, OCEAN_address)

    # Set up dummy return value for the mocked function
    mock_send_encrypted_sapphire_tx.return_value = (
        0,
        "dummy_tx_hash",
    )

    # Sample inputs for send_encrypted_tx
    function_name = "transfer"
    args = [web3_pp.web3_config.owner, 100]
    sender = web3_pp.web3_config.owner
    receiver = web3_pp.web3_config.w3.eth.accounts[1]
    rpc_url = web3_pp.rpc_url
    value = 0
    gasLimit = 10000000
    gasCost = 0
    nonce = 0
    pk = os.getenv("PRIVATE_KEY")

    tx_hash, encrypted_data = contract.send_encrypted_tx(
        function_name,
        args,
        sender,
        receiver,
        pk,
        value,
        gasLimit,
        gasCost,
        nonce,
    )
    assert tx_hash == 0
    assert encrypted_data == "dummy_tx_hash"

    mock_send_encrypted_sapphire_tx.assert_called_once_with(
        pk,
        sender,
        receiver,
        rpc_url,
        value,
        gasLimit,
        OCEAN.contract_instance.encodeABI(fn_name=function_name, args=args),
        gasCost,
        nonce,
    )
