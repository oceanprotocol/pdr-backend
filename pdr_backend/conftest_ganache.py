import os
import pytest

from pdr_backend.models.token import Token
from pdr_backend.models.predictoor_batcher import PredictoorBatcher
from pdr_backend.models.predictoor_contract import PredictoorContract
from pdr_backend.ppss import PPSS, fast_test_yaml_str
from pdr_backend.publisher.publish import publish
from pdr_backend.util.contract import get_address
from pdr_backend.util.web3_config import Web3Config

NETWORK = "development"
CHAIN_ID = 8996
S_PER_EPOCH = 300


@pytest.fixture(scope="session")
def chain_id():
    return CHAIN_ID


@pytest.fixture(scope="session")
def web3_config():
    return _web3_config()


_W3C = None
def _web3_config():
    global _W3C
    if _W3C is None:
        s = fast_test_yaml_str()
        ppss = PPSS(yaml_str=s, network=NETWORK)
        _W3C = ppss.web3_pp.web3_config
    return _W3C
        


@pytest.fixture(scope="session")
def ocean_token() -> Token:
    token_address = get_address(CHAIN_ID, "Ocean")
    return Token(_web3_config(), token_address)


@pytest.fixture(scope="module")
def predictoor_contract():
    web3_config = _web3_config()
    _, _, _, _, logs = publish(
        s_per_epoch=S_PER_EPOCH,
        s_per_subscription=S_PER_EPOCH * 24,
        base="ETH",
        quote="USDT",
        source="kraken",
        timeframe="5m",
        trueval_submitter_addr=config.owner,
        feeCollector_addr=config.owner,
        rate=3,
        cut=0.2,
        web3_config=web3_config,
    )
    dt_addr = logs["newTokenAddress"]
    return PredictoorContract(web3_config, dt_addr)


@pytest.fixture(scope="module")
def predictoor_contract2():
    web3_config = _web3_config()
    _, _, _, _, logs = publish(
        s_per_epoch=S_PER_EPOCH,
        s_per_subscription=S_PER_EPOCH * 24,
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
    return PredictoorContract(web3_config, dt_addr)


# pylint: disable=redefined-outer-name
@pytest.fixture(scope="module")
def predictoor_batcher():
    predictoor_batcher_addr = get_address(CHAIN_ID, "PredictoorHelper")
    return PredictoorBatcher(_web3_config(), predictoor_batcher_addr)
