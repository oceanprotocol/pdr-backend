from unittest.mock import MagicMock, patch
import pytest
from pdr_backend.ppss.ppss import PPSS, fast_test_yaml_str
from pdr_backend.publisher.main import publish_assets


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
    mock_token,
    mock_get_address,
    mock_fund_dev_accounts,
    mock_publish,
    tmpdir,
):
    mock_get_address.return_value = "mock_ocean_address"
    mock_token_instance = MagicMock()
    mock_token.return_value = mock_token_instance

    test_config = fast_test_yaml_str(tmpdir)
    ppss = PPSS(network="development", yaml_str=test_config)

    publish_assets(ppss.web3_pp, ppss.publisher_ss)

    mock_get_address.assert_called_once_with(ppss.web3_pp, "Ocean")
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
        web3_pp=ppss.web3_pp,
    )
