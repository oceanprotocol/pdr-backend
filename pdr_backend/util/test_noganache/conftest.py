from unittest.mock import Mock

from enforce_typing import enforce_types
import pytest

from pdr_backend.ppss.ppss import PPSS, fast_test_yaml_str
from pdr_backend.util.subgraph_predictions import Prediction


@enforce_types
@pytest.fixture(scope="session")
def mock_ppss(tmpdir_factory):
    tmpdir = tmpdir_factory.mktemp("my_tmpdir")
    s = fast_test_yaml_str(tmpdir)
    ppss = PPSS(yaml_str=s, network="development")
    ppss.web3_pp = Mock()
    return ppss


@enforce_types
@pytest.fixture(scope="session")
def sample_predictions():
    return [
        Prediction(
            id="1",
            pair="ADA/USDT",
            timeframe="5m",
            prediction=True,
            stake=0.0500,
            trueval=False,
            timestamp=1701503000,
            source="binance",
            payout=0.0,
            slot=1701503100,
            user="0xaaaa4cb4ff2584bad80ff5f109034a891c3d88dd",
        ),
        Prediction(
            id="2",
            pair="BTC/USDT",
            timeframe="5m",
            prediction=True,
            stake=0.0500,
            trueval=True,
            timestamp=1701589400,
            source="binance",
            payout=0.0,
            slot=1701589500,
            user="0xaaaa4cb4ff2584bad80ff5f109034a891c3d88dd",
        ),
    ]


@enforce_types
@pytest.fixture(scope="session")
def extra_predictions():
    return [
        Prediction(
            id="3",
            pair="ETH/USDT",
            timeframe="5m",
            prediction=True,
            stake=0.0500,
            trueval=True,
            timestamp=1701675800,
            source="binance",
            payout=0.0500,
            slot=1701675900,
            user="0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
        ),
        Prediction(
            id="4",
            pair="BTC/USDT",
            timeframe="1h",
            prediction=True,
            stake=0.0500,
            trueval=False,
            timestamp=1701503100,
            source="binance",
            payout=0.0,
            slot=1701503000,
            user="0xbbbb4cb4ff2584bad80ff5f109034a891c3d88dd",
        ),
        Prediction(
            id="5",
            pair="ADA/USDT",
            timeframe="5m",
            prediction=True,
            stake=0.0500,
            trueval=True,
            timestamp=1701589400,
            source="binance",
            payout=0.0500,
            slot=1701589500,
            user="0xbbbb4cb4ff2584bad80ff5f109034a891c3d88dd",
        ),
        Prediction(
            id="6",
            pair="BNB/USDT",
            timeframe="1h",
            prediction=True,
            stake=0.0500,
            trueval=True,
            timestamp=1701675800,
            source="kraken",
            payout=0.0500,
            slot=1701675900,
            user="0xbbbb4cb4ff2584bad80ff5f109034a891c3d88dd",
        ),
        Prediction(
            id="7",
            pair="ETH/USDT",
            timeframe="1h",
            prediction=True,
            stake=None,
            trueval=False,
            timestamp=1701589400,
            source="binance",
            payout=0.0,
            slot=1701589500,
            user="0xcccc4cb4ff2584bad80ff5f109034a891c3d88dd",
        ),
    ]
