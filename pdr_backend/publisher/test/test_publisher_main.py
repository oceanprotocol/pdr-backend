from unittest.mock import MagicMock, Mock, patch
from pdr_backend.ppss.ppss import PPSS, fast_test_yaml_str
import pytest
from pdr_backend.publisher.main import publish_assets
from pdr_backend.util.web3_config import Web3Config


@pytest.fixture
def mock_getenv_or_exit():
    with patch("pdr_backend.publisher.main.getenv_or_exit") as mock:
        yield mock


@pytest.fixture
def mock_web3_config():
    with patch("pdr_backend.publisher.main.Web3Config") as mock:
        mock_instance = MagicMock(spec=Web3Config)
        mock_instance.w3 = Mock()
        mock_instance.owner = "0x1"
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_token():
    with patch("pdr_backend.publisher.main.Token") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_get_address():
    with patch("pdr_backend.publisher.main.get_address") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock


@pytest.fixture
def mock_fund_dev_accounts():
    with patch("pdr_backend.publisher.main.fund_dev_accounts") as mock:
        yield mock


@pytest.fixture
def mock_publish():
    with patch("pdr_backend.publisher.main.publish") as mock:
        yield mock


# pylint: disable=redefined-outer-name
def test_publish_assets(
    mock_getenv_or_exit,
    mock_web3_config,
    mock_token,
    mock_get_address,
    mock_fund_dev_accounts,
    mock_publish,
    tmpdir,
):
    mock_getenv_or_exit.side_effect = [
        "mock_rpc_url",
        "mock_private_key",
        "mock_fee_collector",
    ]
    mock_web3_config.w3.eth.chain_id = 8996
    mock_get_address.return_value = "mock_ocean_address"
    mock_token_instance = MagicMock()
    mock_token.return_value = mock_token_instance

    test_config = fast_test_yaml_str(tmpdir)
    ppss = PPSS(test_config)
    publish_assets(ppss)

    mock_getenv_or_exit.assert_any_call("RPC_URL")
    mock_getenv_or_exit.assert_any_call("PRIVATE_KEY")
    mock_get_address.assert_called_once_with(8996, "Ocean")
    mock_fund_dev_accounts.assert_called_once()
    mock_publish.assert_any_call(
        s_per_epoch=300,
        s_per_subscription=60 * 60 * 24,
        base="ETH",
        quote="USDT",
        source="binance",
        timeframe="5m",
        trueval_submitter_addr="0xe2DD09d719Da89e5a3D0F2549c7E24566e947260",
        feeCollector_addr="0xe2DD09d719Da89e5a3D0F2549c7E24566e947260",
        rate=3 / (1 + 0.2 + 0.001),
        cut=0.2,
        web3_config=mock_web3_config,
    )
