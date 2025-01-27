import os
from argparse import Namespace
from unittest.mock import Mock, patch

import pytest
from enforce_typing import enforce_types

# below, import in same order as cli_arguments.HELP_LONG
from pdr_backend.cli.cli_module import (
    # main tools
    do_sim,
    do_trader,
    # power tools
    do_multisim,
    do_ohlcv,
    _do_main,
)
from pdr_backend.ppss.ppss import PPSS as PPSSClass


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


class _PPSS_OBJ:
    PPSS = PPSSClass(
        yaml_filename=os.path.abspath("ppss.yaml"),
        network="development",
    )


class _NETWORK:
    NETWORK = "development"


class _LOOKBACK:
    LOOKBACK_HOURS = 24


class _ST:
    ST = "2023-06-22"


class _END:
    END = "2023-06-24"


class _PQDIR:
    PQDIR = "my_lake_data/"


class _FEEDS:
    FEEDS = "0x95222290DD7278Aa3Ddd389Cc1E1d165CC4BAfe4"


class _PDRS:
    PDRS = "0xa5222290DD7278Aa3Ddd389Cc1E1d165CC4BAfe4"


class _NUM:
    NUM = 1


class _ACCOUNT:
    ACCOUNT = "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd"


class _ACCOUNTS:
    ACCOUNTS = "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd"


class _TOKEN_AMOUNT:
    TOKEN_AMOUNT = 13


class _NATIVE_TOKEN:
    NATIVE_TOKEN = True


class _Base:
    def __init__(self, *args, **kwargs):
        pass


class MockArgParser_PPSS(_Base):
    def parse_args(self):
        class MockArgs(Namespace, _PPSS, _PPSS_OBJ):
            pass

        return MockArgs()


class MockArgParser_PPSS_NETWORK(_Base):
    def parse_args(self):
        class MockArgs(Namespace, _PPSS, _NETWORK, _PPSS_OBJ):
            pass

        return MockArgs()


class MockArgParser_APPROACH_PPSS_NETWORK(_Base):
    def __init__(self, approach=_APPROACH):
        self.approach = approach
        super().__init__()

    def parse_args(self):
        class MockArgs(Namespace, self.approach, _PPSS, _NETWORK, _PPSS_OBJ):
            pass

        return MockArgs()


class MockArgParser_PPSS_NETWORK_LOOKBACK(_Base):
    def parse_args(self):
        class MockArgs(Namespace, _PPSS, _NETWORK, _LOOKBACK, _PPSS_OBJ):
            pass

        return MockArgs()


class MockArgParser_ST_END_PQDIR_NETWORK_PPSS_PDRS(_Base):
    def parse_args(self):
        class MockArgs(  # pylint: disable=too-many-ancestors
            Namespace, _ST, _END, _PQDIR, _NETWORK, _PPSS, _PDRS, _PPSS_OBJ
        ):
            pass

        return MockArgs()


class MockArgParser_ST_END_PQDIR_NETWORK_PPSS_FEEDS(_Base):
    def parse_args(self):
        class MockArgs(  # pylint: disable=too-many-ancestors
            Namespace, _ST, _END, _PQDIR, _NETWORK, _PPSS, _FEEDS, _PPSS_OBJ
        ):
            pass

        return MockArgs()


class MockArgParser_NUM(_Base):
    def parse_args(self):
        class MockArgs(Namespace, _NUM):
            pass

        return MockArgs()


class MockArgParser_ACCOUNT_PPSS_NETWORK(_Base):
    def parse_args(self):
        class MockArgs(Namespace, _ACCOUNT, _PPSS, _NETWORK, _PPSS_OBJ):
            pass

        return MockArgs()


class MockArgParser_TOKEN_AMOUNT_ACCOUNTS_TOKEN_PPSS_NETWORK(_Base):
    def parse_args(self):
        # pylint: disable=too-many-ancestors
        class MockArgs(
            Namespace,
            _TOKEN_AMOUNT,
            _ACCOUNTS,
            _PPSS,
            _NETWORK,
            _NATIVE_TOKEN,
            _PPSS_OBJ,
        ):
            pass

        return MockArgs()


@enforce_types
class MockAgent:
    was_run = False

    def __init__(self, ppss: PPSSClass, *args, **kwargs):
        pass

    def run(self, *args, **kwargs):  # pylint: disable=unused-argument
        self.__class__.was_run = True


_CLI_PATH = "pdr_backend.cli.cli_module"

# ===============================================================
# Below, implement tests in same order as cli_arguments.HELP_LONG

# ---------------------------------------------------------------
# test: Main tools


@enforce_types
def test_do_sim(monkeypatch):
    mock_f = Mock()
    monkeypatch.setattr(f"{_CLI_PATH}.SimEngine.run", mock_f)

    do_sim(MockArgParser_PPSS().parse_args())

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
def test_do_ohlcv(monkeypatch):
    mock_f = Mock()
    monkeypatch.setattr(f"{_CLI_PATH}.OhlcvDataFactory.get_mergedohlcv_df", mock_f)

    do_ohlcv(MockArgParser_PPSS_NETWORK().parse_args())
    mock_f.assert_called()




@enforce_types
def test_do_main(capfd):
    with patch("sys.argv", ["pdr", "help"]):
        with pytest.raises(SystemExit):
            _do_main()

    assert "Predictoor tool" in capfd.readouterr().out

    with patch("sys.argv", ["pdr", "undefined_function"]):
        with pytest.raises(SystemExit):
            _do_main()

    assert "Predictoor tool" in capfd.readouterr().out
