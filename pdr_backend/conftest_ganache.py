from unittest.mock import Mock

import pytest

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.contract.predictoor_batcher import PredictoorBatcher
from pdr_backend.contract.feed_contract import FeedContract
from pdr_backend.contract.token import Token
from pdr_backend.ppss.ppss import PPSS, fast_test_yaml_str
from pdr_backend.publisher.publish_asset import publish_asset
from pdr_backend.util.currency_types import Eth

CHAIN_ID = 8996
S_PER_EPOCH = 300


@pytest.fixture(scope="session")  # "session" = invoke once, across all tests
def chain_id():
    return CHAIN_ID


@pytest.fixture(scope="session")
def web3_config():
    return _web3_config()


def _web3_config():
    return _web3_pp().web3_config


@pytest.fixture(scope="session")
def rpc_url():
    return _web3_pp().rpc_url


@pytest.fixture(scope="session")
def web3_pp():
    return _web3_pp()


def _web3_pp():
    return _ppss().web3_pp


@pytest.fixture(scope="session")
def ppss():
    return _ppss()


def _ppss():
    s = fast_test_yaml_str()
    return PPSS(yaml_str=s, network="development")


@pytest.fixture(scope="session")
def OCEAN() -> Token:
    token_address = _web3_pp().get_address("Ocean")
    return Token(_web3_pp(), token_address)


@pytest.fixture(scope="module")  # "module" = invoke once per test module
def predictoor_contract1():
    w3p = _web3_pp()
    w3c = w3p.web3_config
    _, _, _, _, logs = publish_asset(
        s_per_epoch=S_PER_EPOCH,
        s_per_subscription=S_PER_EPOCH * 24,
        feed=ArgFeed("kraken", "close", "ETH/USDT", "5m"),
        trueval_submitter_addr=w3c.owner,
        feeCollector_addr=w3c.owner,
        rate=Eth(3),
        cut=Eth(0.2),
        web3_pp=w3p,
    )
    dt_addr = logs["newTokenAddress"]
    return FeedContract(w3p, dt_addr)


@pytest.fixture(scope="module")
def predictoor_contract2():
    w3p = _web3_pp()
    w3c = w3p.web3_config
    _, _, _, _, logs = publish_asset(
        s_per_epoch=S_PER_EPOCH,
        s_per_subscription=S_PER_EPOCH * 24,
        feed=ArgFeed("kraken", "close", "ETH/USDT", "5m"),
        trueval_submitter_addr=w3c.owner,
        feeCollector_addr=w3c.owner,
        rate=Eth(3),
        cut=Eth(0.2),
        web3_pp=w3p,
    )
    dt_addr = logs["newTokenAddress"]
    return FeedContract(w3p, dt_addr)


@pytest.fixture(scope="module")  # "module" = invoke once per test module
def predictoor_contract_empty():
    w3p = _web3_pp()
    w3c = w3p.web3_config
    _, _, _, _, logs = publish_asset(
        s_per_epoch=S_PER_EPOCH,
        s_per_subscription=S_PER_EPOCH * 24,
        feed=ArgFeed("kraken", "close", "ETH/USDT", "5m"),
        trueval_submitter_addr=w3c.owner,
        feeCollector_addr=w3c.owner,
        rate=Eth(3),
        cut=Eth(0.2),
        web3_pp=w3p,
    )
    dt_addr = logs["newTokenAddress"]
    predictoor_c = FeedContract(w3p, dt_addr)
    predictoor_c.get_exchanges = Mock(return_value=[])

    return predictoor_c


# pylint: disable=redefined-outer-name
@pytest.fixture(scope="module")
def predictoor_batcher():
    w3p = _web3_pp()
    predictoor_batcher_addr = w3p.get_address("PredictoorHelper")
    return PredictoorBatcher(w3p, predictoor_batcher_addr)
