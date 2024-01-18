import os
from argparse import Namespace
from unittest.mock import Mock, patch

import pytest
from enforce_typing import enforce_types

from pdr_backend.cli.cli_module import (
    _do_main,
    do_check_network,
    do_claim_OCEAN,
    do_claim_ROSE,
    do_dfbuyer,
    do_get_predictions_info,
    do_get_predictoors_info,
    do_get_traction_info,
    do_lake,
    do_predictoor,
    do_publisher,
    do_xpmt,
    do_topup,
    do_trader,
    do_trueval,
)
from pdr_backend.ppss.ppss import PPSS


class _APPROACH:
    APPROACH = 1


class _APPROACH2:
    APPROACH = 2


class _APPROACH3:
    APPROACH = 3


class _APPROACH_BAD:
    APPROACH = 99


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
    def __init__(self, approach=_APPROACH):
        self.approach = approach
        super().__init__()

    def parse_args(self):
        class MockArgs(Namespace, self.approach, _PPSS, _NETWORK):
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


_CLI_PATH = "pdr_backend.cli.cli_module"


@enforce_types
def test_do_check_network(monkeypatch):
    mock_f = Mock()
    monkeypatch.setattr(f"{_CLI_PATH}.check_network_main", mock_f)

    do_check_network(MockArgParser_PPSS_NETWORK_LOOKBACK().parse_args())
    mock_f.assert_called()


@enforce_types
def test_do_lake(monkeypatch):
    mock_f = Mock()
    monkeypatch.setattr(f"{_CLI_PATH}.OhlcvDataFactory.get_mergedohlcv_df", mock_f)

    do_lake(MockArgParser_PPSS_NETWORK().parse_args())
    mock_f.assert_called()


@enforce_types
def test_do_claim_OCEAN(monkeypatch):
    mock_f = Mock()
    monkeypatch.setattr(f"{_CLI_PATH}.do_ocean_payout", mock_f)

    do_claim_OCEAN(MockArgParser_PPSS().parse_args())
    mock_f.assert_called()


@enforce_types
def test_do_claim_ROSE(monkeypatch):
    mock_f = Mock()
    monkeypatch.setattr(f"{_CLI_PATH}.do_rose_payout", mock_f)

    do_claim_ROSE(MockArgParser_PPSS().parse_args())
    mock_f.assert_called()


@enforce_types
def test_do_dfbuyer(monkeypatch):
    monkeypatch.setattr(f"{_CLI_PATH}.DFBuyerAgent", MockAgent)

    do_dfbuyer(MockArgParser_PPSS_NETWORK().parse_args())
    assert MockAgent.was_run


@enforce_types
def test_do_get_predictions_info(monkeypatch):
    mock_f = Mock()
    monkeypatch.setattr(f"{_CLI_PATH}.get_predictions_info_main", mock_f)

    do_get_predictions_info(
        MockArgParser_ST_END_PQDIR_NETWORK_PPSS_FEEDS().parse_args()
    )
    mock_f.assert_called()


@enforce_types
def test_do_get_predictoors_info(monkeypatch):
    mock_f = Mock()
    monkeypatch.setattr(f"{_CLI_PATH}.get_predictoors_info_main", mock_f)

    do_get_predictoors_info(MockArgParser_ST_END_PQDIR_NETWORK_PPSS_PDRS().parse_args())
    mock_f.assert_called()


@enforce_types
def test_do_get_traction_info(monkeypatch):
    mock_f = Mock()
    monkeypatch.setattr(f"{_CLI_PATH}.get_traction_info_main", mock_f)

    do_get_traction_info(MockArgParser_ST_END_PQDIR_NETWORK_PPSS_FEEDS().parse_args())
    mock_f.assert_called()


@enforce_types
def test_do_predictoor(monkeypatch):
    monkeypatch.setattr(f"{_CLI_PATH}.PredictoorAgent1", MockAgent)

    do_predictoor(MockArgParser_APPROACH_PPSS_NETWORK().parse_args())
    assert MockAgent.was_run

    monkeypatch.setattr(f"{_CLI_PATH}.PredictoorAgent3", MockAgent)

    do_predictoor(MockArgParser_APPROACH_PPSS_NETWORK(_APPROACH3).parse_args())
    assert MockAgent.was_run

    with pytest.raises(ValueError):
        do_predictoor(MockArgParser_APPROACH_PPSS_NETWORK(_APPROACH_BAD).parse_args())


@enforce_types
def test_do_publisher(monkeypatch):
    mock_f = Mock()
    monkeypatch.setattr(f"{_CLI_PATH}.publish_assets", mock_f)

    do_publisher(MockArgParser_PPSS_NETWORK().parse_args())
    mock_f.assert_called()


@enforce_types
def test_do_topup(monkeypatch):
    mock_f = Mock()
    monkeypatch.setattr(f"{_CLI_PATH}.topup_main", mock_f)

    do_topup(MockArgParser_PPSS_NETWORK().parse_args())
    mock_f.assert_called()


@enforce_types
def test_do_trader(monkeypatch):
    monkeypatch.setattr(f"{_CLI_PATH}.TraderAgent1", MockAgent)

    do_trader(MockArgParser_APPROACH_PPSS_NETWORK().parse_args())
    assert MockAgent.was_run

    monkeypatch.setattr(f"{_CLI_PATH}.TraderAgent2", MockAgent)

    do_trader(MockArgParser_APPROACH_PPSS_NETWORK(_APPROACH2).parse_args())
    assert MockAgent.was_run

    with pytest.raises(ValueError):
        do_trader(MockArgParser_APPROACH_PPSS_NETWORK(_APPROACH_BAD).parse_args())


@enforce_types
def test_do_trueval(monkeypatch):
    monkeypatch.setattr(f"{_CLI_PATH}.TruevalAgent", MockAgent)

    do_trueval(MockArgParser_PPSS_NETWORK().parse_args())
    assert MockAgent.was_run


@enforce_types
def test_do_xpmt(monkeypatch):
    mock_f = Mock()
    monkeypatch.setattr(f"{_CLI_PATH}.XpmtEngine.run", mock_f)

    with patch("pdr_backend.xpmt.xpmt_engine.plt.show"):
        do_xpmt(MockArgParser_PPSS_NETWORK().parse_args())

    mock_f.assert_called()


@enforce_types
def test_do_main(monkeypatch, capfd):
    with patch("sys.argv", ["pdr", "help"]):
        with pytest.raises(SystemExit):
            _do_main()

    assert "Predictoor tool" in capfd.readouterr().out

    with patch("sys.argv", ["pdr", "undefined_function"]):
        with pytest.raises(SystemExit):
            _do_main()

    assert "Predictoor tool" in capfd.readouterr().out

    mock_f = Mock()
    monkeypatch.setattr(f"{_CLI_PATH}.XpmtEngine.run", mock_f)

    with patch("pdr_backend.xpmt.xpmt_engine.plt.show"):
        with patch("sys.argv", ["pdr", "xpmt", "ppss.yaml"]):
            _do_main()

    assert mock_f.called
