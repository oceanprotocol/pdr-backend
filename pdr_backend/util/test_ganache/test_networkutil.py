from unittest.mock import Mock
import os

from enforce_typing import enforce_types
import pytest

from pdr_backend.util.constants import (
    SAPPHIRE_TESTNET_CHAINID,
    SAPPHIRE_MAINNET_CHAINID,
)
from pdr_backend.util.networkutil import (
    is_sapphire_network,
    send_encrypted_tx,
)


@enforce_types
def test_is_sapphire_network():
    assert not is_sapphire_network(0)
    assert is_sapphire_network(SAPPHIRE_TESTNET_CHAINID)
    assert is_sapphire_network(SAPPHIRE_MAINNET_CHAINID)


@enforce_types
def test_send_encrypted_tx(
    mock_send_encrypted_sapphire_tx,  # pylint: disable=redefined-outer-name
    ocean_token,
    web3_config,
):
    # Set up dummy return value for the mocked function
    mock_send_encrypted_sapphire_tx.return_value = (
        0,
        "dummy_tx_hash",
    )
    # Sample inputs for send_encrypted_tx
    function_name = "transfer"
    args = [web3_config.owner, 100]
    pk = os.getenv("PRIVATE_KEY")
    sender = web3_config.owner
    receiver = web3_config.w3.eth.accounts[1]
    rpc_url = "http://localhost:8545"
    value = 0
    gasLimit = 10000000
    gasCost = 0
    nonce = 0
    tx_hash, encrypted_data = send_encrypted_tx(
        ocean_token.contract_instance,
        function_name,
        args,
        pk,
        sender,
        receiver,
        rpc_url,
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
        ocean_token.contract_instance.encodeABI(fn_name=function_name, args=args),
        gasCost,
        nonce,
    )


@pytest.fixture
def mock_send_encrypted_sapphire_tx(monkeypatch):
    mock_function = Mock(return_value=(0, "dummy_tx_hash"))
    monkeypatch.setattr("sapphirepy.wrapper.send_encrypted_sapphire_tx", mock_function)
    return mock_function
