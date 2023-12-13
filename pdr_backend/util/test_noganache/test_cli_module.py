from unittest.mock import Mock
import os

from argparse import Namespace
from enforce_typing import enforce_types

from pdr_backend.ppss.ppss import PPSS
from pdr_backend.util.cli_module import (
    do_check_network,
    do_claim_OCEAN,
    do_claim_ROSE,
    do_dfbuyer,
    do_get_predictions_info,
    do_get_predictoors_info,
    do_get_traction_info,
    do_predictoor,
    do_publisher,
    do_topup,
    do_trader,
    do_trueval,
)


class _APPROACH:
    APPROACH = 1


class _PPSS:
    PPSS_FILE = os.path.abspath("ppss.yaml")


class _NETWORK:
    NETWORK = "development"


class _LOOKBACK:
    LOOKBACK_HOURS = 24


class _ST:
    ST = "2023-06-22"


class _END:
    END = "2023-06-24"


class _PQDIR:
    PQDIR = "my_parquet_data/"


class _FEEDS:
    FEEDS = "0x95222290DD7278Aa3Ddd389Cc1E1d165CC4BAfe4"


class _PDRS:
    PDRS = "0xa5222290DD7278Aa3Ddd389Cc1E1d165CC4BAfe4"


class _Base:
    def __init__(self, *args, **kwargs):
        pass


class MockArgParser_PPSS(_Base):
    def parse_args(self):
        class MockArgs(Namespace, _PPSS):
            pass

        return MockArgs()


class MockArgParser_PPSS_NETWORK(_Base):
    def parse_args(self):
        class MockArgs(Namespace, _PPSS, _NETWORK):
            pass

        return MockArgs()


class MockArgParser_APPROACH_PPSS_NETWORK(_Base):
    def parse_args(self):
        class MockArgs(Namespace, _APPROACH, _PPSS, _NETWORK):
            pass

        return MockArgs()


class MockArgParser_PPSS_NETWORK_LOOKBACK(_Base):
    def parse_args(self):
        class MockArgs(Namespace, _PPSS, _NETWORK, _LOOKBACK):
            pass

        return MockArgs()


class MockArgParser_ST_END_PQDIR_NETWORK_PPSS_PDRS(_Base):
    def parse_args(self):
        class MockArgs(  # pylint: disable=too-many-ancestors
            Namespace, _ST, _END, _PQDIR, _NETWORK, _PPSS, _PDRS
        ):
            pass

        return MockArgs()


class MockArgParser_ST_END_PQDIR_NETWORK_PPSS_FEEDS(_Base):
    def parse_args(self):
        class MockArgs(  # pylint: disable=too-many-ancestors
            Namespace, _ST, _END, _PQDIR, _NETWORK, _PPSS, _FEEDS
        ):
            pass

        return MockArgs()


@enforce_types
class MockAgent:
    was_run = False

    def __init__(self, ppss: PPSS, *args, **kwargs):
        pass

    def run(self, *args, **kwargs):  # pylint: disable=unused-argument
        self.__class__.was_run = True


_CLI_PATH = "pdr_backend.util.cli_module"


@enforce_types
def test_do_check_network(monkeypatch):
    monkeypatch.setattr(
        f"{_CLI_PATH}.CheckNetworkArgParser",
        MockArgParser_PPSS_NETWORK_LOOKBACK,
    )

    mock_f = Mock()
    monkeypatch.setattr(f"{_CLI_PATH}.check_network_main", mock_f)

    do_check_network()
    mock_f.assert_called()


@enforce_types
def test_do_claim_OCEAN(monkeypatch):
    monkeypatch.setattr(f"{_CLI_PATH}.ClaimOceanArgParser", MockArgParser_PPSS)

    mock_f = Mock()
    monkeypatch.setattr(f"{_CLI_PATH}.do_ocean_payout", mock_f)

    do_claim_OCEAN()
    mock_f.assert_called()


@enforce_types
def test_do_claim_ROSE(monkeypatch):
    monkeypatch.setattr(f"{_CLI_PATH}.ClaimRoseArgParser", MockArgParser_PPSS)

    mock_f = Mock()
    monkeypatch.setattr(f"{_CLI_PATH}.do_rose_payout", mock_f)

    do_claim_ROSE()
    mock_f.assert_called()


@enforce_types
def test_do_dfbuyer(monkeypatch):
    monkeypatch.setattr(
        f"{_CLI_PATH}.DfbuyerArgParser",
        MockArgParser_PPSS_NETWORK,
    )

    monkeypatch.setattr(f"{_CLI_PATH}.DFBuyerAgent", MockAgent)

    do_dfbuyer()
    assert MockAgent.was_run


@enforce_types
def test_do_get_predictions_info(monkeypatch):
    monkeypatch.setattr(
        f"{_CLI_PATH}.GetPredictionsInfoArgParser",
        MockArgParser_ST_END_PQDIR_NETWORK_PPSS_FEEDS,
    )

    mock_f = Mock()
    monkeypatch.setattr(f"{_CLI_PATH}.get_predictions_info_main", mock_f)

    do_get_predictions_info()
    mock_f.assert_called()


@enforce_types
def test_do_get_predictoors_info(monkeypatch):
    monkeypatch.setattr(
        f"{_CLI_PATH}.GetPredictoorsInfoArgParser",
        MockArgParser_ST_END_PQDIR_NETWORK_PPSS_PDRS,
    )

    mock_f = Mock()
    monkeypatch.setattr(f"{_CLI_PATH}.get_predictoors_info_main", mock_f)

    do_get_predictoors_info()
    mock_f.assert_called()


@enforce_types
def test_do_get_traction_info(monkeypatch):
    monkeypatch.setattr(
        f"{_CLI_PATH}.GetTractionInfoArgParser",
        MockArgParser_ST_END_PQDIR_NETWORK_PPSS_FEEDS,
    )

    mock_f = Mock()
    monkeypatch.setattr(f"{_CLI_PATH}.get_traction_info_main", mock_f)

    do_get_traction_info()
    mock_f.assert_called()


@enforce_types
def test_do_predictoor(monkeypatch):
    monkeypatch.setattr(
        f"{_CLI_PATH}.PredictoorArgParser",
        MockArgParser_APPROACH_PPSS_NETWORK,
    )

    monkeypatch.setattr(f"{_CLI_PATH}.PredictoorAgent1", MockAgent)

    do_predictoor()
    assert MockAgent.was_run


@enforce_types
def test_do_publisher(monkeypatch):
    monkeypatch.setattr(
        f"{_CLI_PATH}.PublisherArgParser",
        MockArgParser_PPSS_NETWORK,
    )

    mock_f = Mock()
    monkeypatch.setattr(f"{_CLI_PATH}.publish_assets", mock_f)

    do_publisher()
    mock_f.assert_called()


@enforce_types
def test_do_topup(monkeypatch):
    monkeypatch.setattr(
        f"{_CLI_PATH}.TopupArgParser",
        MockArgParser_PPSS_NETWORK,
    )

    mock_f = Mock()
    monkeypatch.setattr(f"{_CLI_PATH}.topup_main", mock_f)

    do_topup()
    mock_f.assert_called()


@enforce_types
def test_do_trader(monkeypatch):
    monkeypatch.setattr(
        f"{_CLI_PATH}.TraderArgParser",
        MockArgParser_APPROACH_PPSS_NETWORK,
    )

    monkeypatch.setattr(f"{_CLI_PATH}.TraderAgent1", MockAgent)

    do_trader()
    assert MockAgent.was_run


@enforce_types
def test_do_trueval(monkeypatch):
    monkeypatch.setattr(
        f"{_CLI_PATH}.TruevalArgParser",
        MockArgParser_PPSS_NETWORK,
    )

    monkeypatch.setattr(f"{_CLI_PATH}.TruevalAgent", MockAgent)

    do_trueval()
    assert MockAgent.was_run
