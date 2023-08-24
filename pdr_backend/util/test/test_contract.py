import os
from pathlib import Path
import time
from unittest.mock import patch, Mock
from enforce_typing import enforce_types
import pytest
from pytest import approx

from pdr_backend.publisher.publish import publish
from pdr_backend.util.constants import (
    SAPPHIRE_TESTNET_CHAINID,
    SAPPHIRE_MAINNET_CHAINID,
)
from pdr_backend.util.contract import (
    is_sapphire_network,
    send_encrypted_tx,
    ERC721Factory,
    FixedRate,
    Web3Config,
    Token,
    PredictoorContract,
    get_contract_filename,
    get_address,
    get_contract_abi,
    get_addresses,
)

SECONDS_PER_EPOCH = 300



def test_get_id(predictoor_contract):
    id = predictoor_contract.getid()
    assert id == 3


def test_get_address(chain_id):
    result = get_address(chain_id, "Ocean")
    assert result is not None


def test_get_addresses(chain_id):
    result = get_addresses(chain_id)
    assert result is not None


def test_get_contract_abi():
    result = get_contract_abi("ERC20Template3")
    assert len(result) > 0 and isinstance(result, list)


def test_get_contract_filename():
    result = get_contract_filename("ERC20Template3")
    assert result is not None and isinstance(result, Path)


# --------------------


@pytest.fixture(autouse=True)
def run_before_each_test():
    # This setup code will be run before each test
    print("Setting up!")


@pytest.fixture(scope="module")
def predictoor_contract(rpc_url, private_key):
    config = Web3Config(rpc_url, private_key)
    _, _, _, _, logs = publish(
        s_per_epoch=SECONDS_PER_EPOCH,
        s_per_subscription=SECONDS_PER_EPOCH * 24,
        base="ETH",
        quote="USDT",
        source="kraken",
        timeframe="5m",
        trueval_submitter_addr=config.owner,
        feeCollector_addr=config.owner,
        rate=3,
        cut=0.2,
        web3_config=config,
    )
    dt_addr = logs["newTokenAddress"]
    return PredictoorContract(config, dt_addr)
