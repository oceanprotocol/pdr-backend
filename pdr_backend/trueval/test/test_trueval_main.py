import os
import pytest
from unittest.mock import patch, Mock, MagicMock
from pdr_backend.models.contract_data import ContractData
from pdr_backend.models.slot import Slot
from pdr_backend.trueval.main import TruevalAgent, main
from pdr_backend.util.web3_config import Web3Config
from pdr_backend.trueval.trueval_config import TruevalConfig
from pdr_backend.util.env import parse_filters


def test_new_config():
    config = TruevalConfig()
    assert config.rpc_url == os.getenv("RPC_URL")
    assert config.subgraph_url == os.getenv("SUBGRAPH_URL")
    assert config.private_key == os.getenv("PRIVATE_KEY")
    assert config.sleep_time == int(os.getenv("SLEEP_TIME", "30"))
    assert config.batch_size == int(os.getenv("BATCH_SIZE", "30"))

    filters = parse_filters()
    assert config.pair_filters == filters[0]
    assert config.timeframe_filter == filters[1]
    assert config.source_filter == filters[2]
    assert config.owner_addresses == filters[3]


def test_new_agent(trueval_config):
    agent = TruevalAgent(trueval_config)
    assert agent.config == trueval_config


def test_process_slot(agent, slot, predictoor_contract):
    with patch.object(
        agent, "get_and_submit_trueval", return_value={"tx": "0x123"}
    ) as mock_submit:
        result = agent.process_slot(slot)
        assert result == {"tx": "0x123"}
        mock_submit.assert_called()


def test_get_contract_info_caching(agent, predictoor_contract):
    agent.get_contract_info("0x1")
    agent.get_contract_info("0x1")
    assert predictoor_contract.call_count == 1
    predictoor_contract.assert_called_once_with(agent.config.web3_config, "0x1")


def test_submit_trueval_mocked_price_down(agent, slot, predictoor_contract):
    with patch("ccxt.kraken.fetch_ohlcv", mock_fetch_ohlcv_down):
        result = agent.get_and_submit_trueval(
            slot, predictoor_contract.return_value, 60
        )
        assert result == {"tx": "0x123"}
        predictoor_contract.return_value.submit_trueval.assert_called_once_with(
            False, 1692943200, False, True
        )


def test_submit_trueval_mocked_price_up(agent, slot, predictoor_contract):
    with patch("ccxt.kraken.fetch_ohlcv", mock_fetch_ohlcv_up):
        result = agent.get_and_submit_trueval(
            slot, predictoor_contract.return_value, 60
        )
        assert result == {"tx": "0x123"}
        predictoor_contract.return_value.submit_trueval.assert_called_once_with(
            True, 1692943200, False, True
        )


def test_take_step(slot, agent):
    mocked_env = {
        "SLEEP_TIME": "1",
        "BATCH_SIZE": "1",
    }

    mocked_web3_config = MagicMock()

    with patch.dict("os.environ", mocked_env), patch.object(
        agent.config, "web3_config", new=mocked_web3_config
    ), patch("time.sleep"), patch.object(
        TruevalConfig, "get_pending_slots", return_value=[slot]
    ), patch.object(
        TruevalAgent, "process_slot"
    ) as ps_mock:
        agent.take_step()

    ps_mock.assert_called_once_with(slot)


def test_run(slot, agent):
    mocked_env = {
        "SLEEP_TIME": "1",
        "BATCH_SIZE": "1",
    }

    mocked_web3_config = MagicMock()

    with patch.dict("os.environ", mocked_env), patch.object(
        agent.config, "web3_config", new=mocked_web3_config
    ), patch("time.sleep"), patch.object(
        TruevalConfig, "get_pending_slots", return_value=[slot]
    ), patch.object(
        TruevalAgent, "process_slot"
    ) as ps_mock:
        agent.run(True)

    ps_mock.assert_called_once_with(slot)


def test_main(slot):
    mocked_env = {
        "SLEEP_TIME": "1",
        "BATCH_SIZE": "1",
    }

    mocked_web3_config = MagicMock()

    with patch.dict("os.environ", mocked_env), patch(
        "pdr_backend.trueval.trueval_config.Web3Config", return_value=mocked_web3_config
    ), patch("time.sleep"), patch.object(
        TruevalConfig, "get_pending_slots", return_value=[slot]
    ), patch.object(
        TruevalAgent, "process_slot"
    ) as ps_mock:
        main(True)

    ps_mock.assert_called_once_with(slot)


# ------------------------------------------------------------
### Fixtures


@pytest.fixture()
def trueval_config():
    return TruevalConfig()


@pytest.fixture()
def agent(trueval_config):
    return TruevalAgent(trueval_config)


@pytest.fixture()
def slot():
    contract_data = ContractData(
        name="ETH-USDT",
        address="0xBE5449a6A97aD46c8558A3356267Ee5D2731ab5e",
        symbol="ETH-USDT",
        seconds_per_epoch=60,
        seconds_per_subscription=500,
        pair="eth-usdt",
        source="kraken",
        timeframe="5m",
        trueval_submit_timeout=100,
        owner="0xowner",
    )

    return Slot(
        contract=contract_data,
        slot=1692943200,
    )


@pytest.fixture()
def predictoor_contract():
    with patch(
        "pdr_backend.trueval.main.PredictoorContract", return_value=mock_contract()
    ) as mock_predictoor_contract:
        yield mock_predictoor_contract


@pytest.fixture(autouse=True)
def set_env_vars():
    original_value = os.environ.get("OWNER_ADDRS", None)
    os.environ["OWNER_ADDRS"] = "0xBE5449a6A97aD46c8558A3356267Ee5D2731ab5e"
    yield
    if original_value is not None:
        os.environ["OWNER_ADDRS"] = original_value
    else:
        os.environ.pop("OWNER_ADDRS", None)


# ------------------------------------------------------------
### Mocks


def mock_contract(*args, **kwarg):
    m = Mock()
    m.get_secondsPerEpoch.return_value = 60
    m.submit_trueval.return_value = {"tx": "0x123"}
    m.contract_address = "0x1"
    return m


def mock_fetch_ohlcv_down(*args, **kwargs):
    since = kwargs.get("since")
    if since == 1692943140:
        return [[None, 200]]
    elif since == 1692943200:
        return [[None, 100]]
    else:
        raise ValueError("Invalid timestamp")


def mock_fetch_ohlcv_up(*args, **kwargs):
    since = kwargs.get("since")
    if since == 1692943140:
        return [[None, 100]]
    elif since == 1692943200:
        return [[None, 200]]
    else:
        raise ValueError("Invalid timestamp")
