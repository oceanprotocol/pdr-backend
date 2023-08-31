import os
import pytest

from pdr_backend.models.token import Token
from pdr_backend.models.predictoor_helper import PredictoorHelper
from pdr_backend.models.predictoor_contract import PredictoorContract
from pdr_backend.publisher.publish import publish
from pdr_backend.util.contract import get_address
from pdr_backend.util.web3_config import Web3Config

_BARGE_ADDRESS_FILE = "~/.ocean/ocean-contracts/artifacts/address.json"

SECONDS_PER_EPOCH = 300
os.environ["MODELDIR"] = "my_model_dir"


@pytest.fixture(autouse=True)
def barge_address_file():
    os.environ["ADDRESS_FILE"] = os.path.expanduser(_BARGE_ADDRESS_FILE)


@pytest.fixture(scope="session")
def rpc_url():
    return _rpc_url()


def _rpc_url():
    return os.environ.get("TEST_RPC_URL", default="http://127.0.0.1:8545")


@pytest.fixture(scope="session")
def private_key():
    return _private_key()


def _private_key():
    return os.environ.get(
        "TEST_PRIVATE_KEY",
        default="0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58",
    )


@pytest.fixture(scope="session")
def chain_id():
    return _chain_id()


def _chain_id():
    return 8996


@pytest.fixture(scope="session")
def web3_config():
    return _web3_config()


def _web3_config():
    return Web3Config(_rpc_url(), _private_key())


@pytest.fixture(scope="session")
def ocean_token() -> Token:
    token_address = get_address(_chain_id(), "Ocean")
    return Token(_web3_config(), token_address)


@pytest.fixture(scope="module")
def predictoor_contract():
    config = Web3Config(_rpc_url(), _private_key())
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
    config = Web3Config(_rpc_url(), _private_key())
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
def predictoor_helper():
    predictoor_helper_addr = get_address(_chain_id(), "PredictoorHelper")
    predictoor_helper = PredictoorHelper(_web3_config(), predictoor_helper_addr)
    return predictoor_helper
