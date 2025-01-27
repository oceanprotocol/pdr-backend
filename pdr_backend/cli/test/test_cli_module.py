import os
from argparse import Namespace
from unittest.mock import Mock, patch

import pytest
from enforce_typing import enforce_types

# below, import in same order as cli_arguments.HELP_LONG
from pdr_backend.cli.cli_module import (
    do_sim,
    do_ohlcv,
    _do_main,
)
from pdr_backend.ppss.ppss import PPSS as PPSSClass

class _PPSS:
    PPSS_FILE = os.path.abspath("ppss.yaml")


class _PPSS_OBJ:
    PPSS = PPSSClass(
        yaml_filename=os.path.abspath("ppss.yaml"),
    )


class _LOOKBACK:
    LOOKBACK_HOURS = 24


class _ST:
    ST = "2023-06-22"


class _END:
    END = "2023-06-24"


class _PQDIR:
    PQDIR = "my_lake_data/"

class _NUM:
    NUM = 1

class _Base:
    def __init__(self, *args, **kwargs):
        pass


class MockArgParser_PPSS(_Base):
    def parse_args(self):
        class MockArgs(Namespace, _PPSS, _PPSS_OBJ):
            pass

        return MockArgs()


class MockArgParser_APPROACH_PPSS(_Base):
    def __init__(self, approach=_APPROACH):
        self.approach = approach
        super().__init__()

    def parse_args(self):
        class MockArgs(Namespace, self.approach, _PPSS, _PPSS_OBJ):
            pass

        return MockArgs()


class MockArgParser_ST_END_PQDIR_PPSS_PDRS(_Base):
    def parse_args(self):
        class MockArgs(  # pylint: disable=too-many-ancestors
            Namespace, _ST, _END, _PQDIR, _PPSS, _PDRS, _PPSS_OBJ
        ):
            pass

        return MockArgs()


class MockArgParser_ST_END_PQDIR_PPSS_FEEDS(_Base):
    def parse_args(self):
        class MockArgs(  # pylint: disable=too-many-ancestors
            Namespace, _ST, _END, _PQDIR, _PPSS, _FEEDS, _PPSS_OBJ
        ):
            pass

        return MockArgs()


class MockArgParser_NUM(_Base):
    def parse_args(self):
        class MockArgs(Namespace, _NUM):
            pass

        return MockArgs()



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
