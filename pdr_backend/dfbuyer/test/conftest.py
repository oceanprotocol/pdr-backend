from unittest.mock import MagicMock, patch

import pytest

from pdr_backend.contract.predictoor_batcher import mock_predictoor_batcher
from pdr_backend.dfbuyer.dfbuyer_agent import DFBuyerAgent
from pdr_backend.ppss.ppss import mock_feed_ppss
from pdr_backend.ppss.web3_pp import inplace_mock_feedgetters
from pdr_backend.util.constants import MAX_UINT, ZERO_ADDRESS

PATH = "pdr_backend.dfbuyer.dfbuyer_agent"


@pytest.fixture()
def mock_token():
    with patch(f"pdr_backend.ppss.web3_pp.Token") as mock_token_class:
        mock_token_instance = MagicMock()
        mock_token_instance.allowance.return_value = MAX_UINT
        mock_token_class.return_value = mock_token_instance
        yield mock_token_class


_MOCK_FEED_PPSS = None  # (feed, ppss)


def _mock_feed_ppss():
    global _MOCK_FEED_PPSS
    if _MOCK_FEED_PPSS is None:
        feed, ppss = mock_feed_ppss("5m", "binance", "BTC/USDT")
        inplace_mock_feedgetters(ppss.web3_pp, feed)  # mock publishing feeds
        _MOCK_FEED_PPSS = (feed, ppss)
    return _MOCK_FEED_PPSS


@pytest.fixture
def mock_ppss():
    _, ppss = _mock_feed_ppss()
    return ppss


@pytest.fixture
def mock_PredictoorBatcher(mock_ppss):  # pylint: disable=redefined-outer-name
    with patch(f"{PATH}.PredictoorBatcher") as mock:
        mock.return_value = mock_predictoor_batcher(mock_ppss.web3_pp)
        yield mock


@pytest.fixture
def mock_dfbuyer_agent(  # pylint: disable=unused-argument, redefined-outer-name
    mock_token,
    mock_ppss,
    mock_PredictoorBatcher,
):
    with patch.object(mock_ppss.web3_pp, "get_address", return_value=ZERO_ADDRESS):
        return DFBuyerAgent(mock_ppss)
