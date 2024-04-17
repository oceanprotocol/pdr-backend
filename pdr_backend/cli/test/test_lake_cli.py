import os
from argparse import Namespace
from unittest.mock import Mock, patch

import pytest
from enforce_typing import enforce_types

from pdr_backend.cli.lake_cli import (
    PersistentDataStore,
    do_etl_drop,
    do_etl_update,
    do_lake_describe,
    do_lake_query,
    do_lake_subcommand,
    do_raw_drop,
    do_raw_update,
    get_lake_dir,
)
from pdr_backend.util.time_types import UnixTimeMs


@enforce_types
def test_do_lake_subcommand():
    with patch("pdr_backend.cli.lake_cli.do_lake_describe") as mock_do_lake_describe:
        do_lake_subcommand(["describe", "lake_data"])

    mock_do_lake_describe.assert_called_once()

    with patch("pdr_backend.cli.lake_cli.do_lake_query") as mock_do_lake_query:
        do_lake_subcommand(["query", "lake_data", "query"])

    mock_do_lake_query.assert_called_once()


@enforce_types
def test_get_lake_dir():
    abs_path = os.path.abspath("lake_data")
    assert get_lake_dir("lake_data") == abs_path
    assert get_lake_dir(os.path.abspath("lake_data")) == abs_path


@enforce_types
def test_do_lake_describe():
    lake_dir = os.path.abspath("lake_data")
    args = Namespace()
    args.subcommand = "describe"
    args.LAKE_DIR = lake_dir

    with patch("pdr_backend.cli.lake_cli.LakeInfo") as mock_lake_info:
        do_lake_describe(lake_dir, args)

    mock_lake_info.assert_called_once_with(lake_dir)


@enforce_types
def test_do_lake_query(caplog):
    lake_dir = os.path.abspath("lake_data")
    query = "SELECT * FROM table"

    args = Namespace()
    args.LAKE_DIR = lake_dir
    args.QUERY = query

    mock_pds = Mock()
    mock_pds.query_data.return_value = "query result"

    with patch("pdr_backend.cli.lake_cli.PersistentDataStore", return_value=mock_pds):
        do_lake_query(query, args)

    mock_pds.query_data.assert_called_once_with(query)

    mock_pds_err = Mock()
    mock_pds_err.query_data.side_effect = Exception("boom!")

    with patch(
        "pdr_backend.cli.lake_cli.PersistentDataStore", return_value=mock_pds_err
    ):
        do_lake_query(query, args)

    assert "Error querying lake: boom!" in caplog.text


@enforce_types
def test_do_lake_raw_delegation():
    args = ["raw", "drop", "lake_data", "2021-01-01"]

    pds_mock = Mock()

    with patch("pdr_backend.cli.lake_cli.do_raw_drop") as raw_drop:
        with patch(
            "pdr_backend.cli.lake_cli.PersistentDataStore", return_value=pds_mock
        ):
            do_lake_subcommand(args)

    assert raw_drop.called

    args.append("2021-01-01")
    with pytest.raises(SystemExit):
        # raw does not recognize the extra END argument
        do_lake_subcommand(args)

    args[1] = "update"

    with patch("pdr_backend.cli.lake_cli.do_raw_update") as raw_update:
        with patch("pdr_backend.cli.lake_cli.PersistentDataStore", return_value=Mock()):
            do_lake_subcommand(args)

    assert raw_update.called

    args[3] = "invalid date"

    with pytest.raises(SystemExit):
        # end date is invalid
        do_lake_subcommand(args)


@enforce_types
def test_do_lake_etl_delegation():
    args = ["etl", "drop", "lake_data", "2021-01-01"]

    pds_mock = Mock()

    with patch("pdr_backend.cli.lake_cli.do_etl_drop") as etl_drop:
        with patch(
            "pdr_backend.cli.lake_cli.PersistentDataStore", return_value=pds_mock
        ):
            do_lake_subcommand(args)

    assert etl_drop.called
    assert isinstance(etl_drop.call_args[0][1].ST, UnixTimeMs)

    args.append("2021-01-01")
    with pytest.raises(SystemExit):
        # raw does not recognize the extra END argument
        do_lake_subcommand(args)

    args[1] = "update"

    with patch("pdr_backend.cli.lake_cli.do_etl_update") as etl_update:
        with patch("pdr_backend.cli.lake_cli.PersistentDataStore", return_value=Mock()):
            do_lake_subcommand(args)

    assert etl_update.called


@enforce_types
def test_do_lake_raw_drop(capsys):
    args = Namespace()
    args.ST = UnixTimeMs.from_timestr("2021-01-01")

    pds = Mock(spec=PersistentDataStore)
    do_raw_drop(pds, args)
    assert "TODO: start ms = 1609459200000" in capsys.readouterr().out


@enforce_types
def test_do_lake_raw_update(capsys):
    args = Namespace()
    args.ST = UnixTimeMs.from_timestr("2021-01-01")
    args.END = UnixTimeMs.from_timestr("2021-01-02")

    pds = Mock(spec=PersistentDataStore)
    do_raw_update(pds, args)
    assert (
        "TODO: start ms = 1609459200000, end ms = 1609545600000"
        in capsys.readouterr().out
    )


@enforce_types
def test_do_lake_etl_drop(capsys):
    args = Namespace()
    args.ST = UnixTimeMs.from_timestr("2021-01-01")

    pds = Mock(spec=PersistentDataStore)
    do_etl_drop(pds, args)
    assert "TODO: start ms = 1609459200000" in capsys.readouterr().out


@enforce_types
def test_do_lake_etl_update(capsys):
    args = Namespace()
    args.ST = UnixTimeMs.from_timestr("2021-01-01")
    args.END = UnixTimeMs.from_timestr("2021-01-02")

    pds = Mock(spec=PersistentDataStore)
    do_etl_update(pds, args)
    assert (
        "TODO: start ms = 1609459200000, end ms = 1609545600000"
        in capsys.readouterr().out
    )
