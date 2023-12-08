from unittest.mock import Mock

from enforce_typing import enforce_types
import pytest

from pdr_backend.ppss.ppss import PPSS, fast_test_yaml_str
from pdr_backend.ppss.web3_pp import Web3PP
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
def mock_ppss_web3(tmpdir_factory):
    tmpdir = tmpdir_factory.mktemp("my_tmpdir")
    s = fast_test_yaml_str(tmpdir)
    ppss = PPSS(yaml_str=s, network="development")
    ppss.web3_pp = _web3_pp()
    return ppss


# pylint: disable=line-too-long
@enforce_types
def _web3_pp():
    return Web3PP(
        {
            "sapphire-mainnet": {
                "subgraph_url": "https://v4.subgraph.sapphire-mainnet.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph",
                "owner_addrs": "0x4ac2e51f9b1b0ca9e000dfe6032b24639b172703",
            }
        },
        network="sapphire-mainnet",
    )


@enforce_types
@pytest.fixture(scope="session")
def sample_first_predictions():
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
def sample_second_predictions():
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
        Prediction(
            id="8",
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
    ]


@enforce_types
@pytest.fixture(scope="session")
def sample_daily_predictions():
    return [
        Prediction(
            id="9",
            pair="ETH/USDT",
            timeframe="5m",
            prediction=True,
            stake=0.0500,
            trueval=True,
            timestamp=1698865200,
            source="binance",
            payout=0.0500,
            slot=1698865200,  # Nov 01
            user="0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
        ),
        Prediction(
            id="10",
            pair="BTC/USDT",
            timeframe="1h",
            prediction=True,
            stake=0.0500,
            trueval=False,
            timestamp=1698951600,
            source="binance",
            payout=0.0,
            slot=1698951600,  # Nov 02
            user="0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
        ),
        Prediction(
            id="11",
            pair="ADA/USDT",
            timeframe="5m",
            prediction=True,
            stake=0.0500,
            trueval=True,
            timestamp=1699038000,
            source="binance",
            payout=0.0500,
            slot=1699038000,  # Nov 03
            user="0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
        ),
        Prediction(
            id="12",
            pair="BNB/USDT",
            timeframe="1h",
            prediction=True,
            stake=0.0500,
            trueval=True,
            timestamp=1699124400,
            source="kraken",
            payout=0.0500,
            slot=1699124400,  # Nov 04
            user="0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
        ),
        Prediction(
            id="13",
            pair="ETH/USDT",
            timeframe="1h",
            prediction=True,
            stake=None,
            trueval=False,
            timestamp=1699214400,
            source="binance",
            payout=0.0,
            slot=1701589500,  # Nov 05
            user="0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
        ),
        Prediction(
            id="14",
            pair="ETH/USDT",
            timeframe="5m",
            prediction=True,
            stake=0.0500,
            trueval=True,
            timestamp=1699300800,
            source="binance",
            payout=0.0500,
            slot=1699300800,  # Nov 06
            user="0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
        ),
    ]
