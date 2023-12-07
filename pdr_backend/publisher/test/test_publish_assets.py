import os
from unittest.mock import Mock

from enforce_typing import enforce_types

from pdr_backend.ppss.web3_pp import mock_web3_pp
from pdr_backend.ppss.publisher_ss import mock_publisher_ss
from pdr_backend.publisher.publish_assets import publish_assets

_PATH = "pdr_backend.publisher.publish_assets"


@enforce_types
def test_publish_assets_dev(monkeypatch):
    mock_publish_asset, web3_pp = _setup_and_publish("development", monkeypatch)

    n_calls = len(mock_publish_asset.call_args_list)
    assert n_calls == 1 * 3

    mock_publish_asset.assert_any_call(
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
        web3_pp=web3_pp,
    )


@enforce_types
def test_publish_assets_sapphire(monkeypatch):
    mock_publish_asset, _ = _setup_and_publish("sapphire-mainnet", monkeypatch)

    n_calls = len(mock_publish_asset.call_args_list)
    assert n_calls == 2 * 10


def _setup_and_publish(network, monkeypatch):
    if os.getenv("NETWORK_OVERRIDE"):
        monkeypatch.delenv("NETWORK_OVERRIDE")

    web3_pp = mock_web3_pp(network)
    publisher_ss = mock_publisher_ss()

    monkeypatch.setattr(f"{_PATH}.get_address", Mock())

    mock_publish_asset = Mock()
    monkeypatch.setattr(f"{_PATH}.publish_asset", mock_publish_asset)

    # main call
    publish_assets(web3_pp, publisher_ss)

    return mock_publish_asset, web3_pp
