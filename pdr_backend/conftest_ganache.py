import os
import pytest

from pdr_backend.models.token import Token
from pdr_backend.models.predictoor_batcher import PredictoorBatcher
from pdr_backend.models.predictoor_contract import PredictoorContract
from pdr_backend.publisher.publish import publish
from pdr_backend.util.contract import get_address
from pdr_backend.util.web3_config import Web3Config

SECONDS_PER_EPOCH = 300
os.environ["MODELDIR"] = "my_model_dir"


@pytest.fixture(scope="session")
def chain_id():
    return _chain_id()


def _chain_id():
    return 8996


@pytest.fixture(scope="session")
def web3_config():
    return _web3_config()


def _web3_config():
    return Web3Config(os.getenv("RPC_URL"), os.getenv("PRIVATE_KEY"))


@pytest.fixture(scope="session")
def ocean_token() -> Token:
    token_address = get_address(_chain_id(), "Ocean")
    return Token(_web3_config(), token_address)


@pytest.fixture(scope="module")
def predictoor_contract():
    config = Web3Config(os.getenv("RPC_URL"), os.getenv("PRIVATE_KEY"))
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


@pytest.fixture(scope="module")
def predictoor_contract2():
    config = Web3Config(os.getenv("RPC_URL"), os.getenv("PRIVATE_KEY"))
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


# pylint: disable=redefined-outer-name
@pytest.fixture(scope="module")
def predictoor_batcher():
    predictoor_batcher_addr = get_address(_chain_id(), "PredictoorHelper")
    return PredictoorBatcher(_web3_config(), predictoor_batcher_addr)
