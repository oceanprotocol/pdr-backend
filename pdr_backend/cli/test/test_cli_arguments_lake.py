import os
from unittest.mock import patch

import pytest
from enforce_typing import enforce_types

from pdr_backend.cli.cli_arguments_lake import str_as_abspath
from pdr_backend.cli.cli_module_lake import do_lake_subcommand


@enforce_types
def test_str_as_abspath():
    abs_path = os.path.abspath("lake_data")
    assert str_as_abspath("lake_data") == abs_path
    assert str_as_abspath(os.path.abspath("lake_data")) == abs_path


@enforce_types
def test_timestr_args(capsys):
    args = ["raw", "drop", "ppss.yaml", "network", "invalid_date"]

    with pytest.raises(SystemExit):
        do_lake_subcommand(args)

    captured = capsys.readouterr()
    assert "error: argument ST: invalid timestr value: 'invalid_date'" in captured.err

    # drop does not recognize the end date as a valid argument
    args = ["raw", "drop", "ppss.yaml", "network", "2021-01-01", "2021-01-02"]
    with pytest.raises(SystemExit):
        do_lake_subcommand(args)

    captured = capsys.readouterr()
    assert "error: unrecognized arguments: 2021-01-02" in captured.err

    # start date can not be now
    args = ["raw", "drop", "ppss.yaml", "network", "now"]
    with pytest.raises(SystemExit):
        do_lake_subcommand(args)

    captured = capsys.readouterr()
    assert "error: argument ST: invalid timestr value: 'now'" in captured.err

    args = [
        "raw",
        "update",
        "ppss.yaml",
        "sapphire-mainnet",
        "2021-01-01",
        "invalid_end_date",
    ]

    with pytest.raises(SystemExit):
        do_lake_subcommand(args)

    captured = capsys.readouterr()
    assert (
        "error: argument END: invalid timestr_or_now value: 'invalid_end_date'"
        in captured.err
    )

    args[5] = "now"

    with patch("pdr_backend.cli.cli_module_lake.do_lake_raw_update") as raw_update:
        do_lake_subcommand(args)

    assert raw_update.called
