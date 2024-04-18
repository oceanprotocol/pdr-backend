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
    str_as_abspath,
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
def test_str_as_abspath():
    abs_path = os.path.abspath("lake_data")
    assert str_as_abspath("lake_data") == abs_path
    assert str_as_abspath(os.path.abspath("lake_data")) == abs_path


@enforce_types
def test_do_lake_describe():
    lake_dir = os.path.abspath("lake_data")
    args = Namespace()
    args.subcommand = "describe"
    args.LAKE_DIR = lake_dir

    with patch("pdr_backend.cli.lake_cli.LakeInfo") as mock_lake_info:
        do_lake_describe(args)

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
        do_lake_query(args)

    mock_pds.query_data.assert_called_once_with(query)

    mock_pds_err = Mock()
    mock_pds_err.query_data.side_effect = Exception("boom!")

    with patch(
        "pdr_backend.cli.lake_cli.PersistentDataStore", return_value=mock_pds_err
    ):
        do_lake_query(args)

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

    args[3] = "invalid date"

    with pytest.raises(SystemExit):
        # start date is invalid
        do_lake_subcommand(args)

    args.append("2021-01-01")
    with pytest.raises(SystemExit):
        # raw does not recognize the extra END argument
        do_lake_subcommand(args)

    args = [
        "raw",
        "update",
        "ppss.yaml",
        "sapphire-mainnet",
        "2021-01-01",
        "2021-01-02",
    ]

    with patch("pdr_backend.cli.lake_cli.do_raw_update") as raw_update:
        with patch("pdr_backend.cli.lake_cli.PersistentDataStore", return_value=Mock()):
            do_lake_subcommand(args)

    assert raw_update.called


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
    assert isinstance(etl_drop.call_args[0][0].ST, UnixTimeMs)

    args.append("2021-01-01")
    with pytest.raises(SystemExit):
        # raw does not recognize the extra END argument
        do_lake_subcommand(args)

    """
    args[1] = "update"

    with patch("pdr_backend.cli.lake_cli.do_etl_update") as etl_update:
        with patch("pdr_backend.cli.lake_cli.PersistentDataStore", return_value=Mock()):
            do_lake_subcommand(args)

    assert etl_update.called
    """


@enforce_types
def test_do_lake_raw_drop(tmpdir, caplog):
    args = Namespace()
    args.ST = UnixTimeMs.from_timestr("2021-01-01")  # 1609459200000
    args.LAKE_DIR = ""

    one_day = 1000 * 60 * 60 * 24
    first_entry_ts = 1609459200000 - one_day * 3  # 3 days before ST

    pds = PersistentDataStore(str(tmpdir))
    pds.query_data("CREATE TABLE _temp_test1 (id INT, timestamp INT64)")

    for i in range(5):
        pds.query_data(
            f"INSERT INTO _temp_test1 VALUES ({i}, {first_entry_ts + i * one_day})"
        )

    pds.query_data("CREATE TABLE test2 (id INT, timestamp INT64)")

    for i in range(5):
        pds.query_data(
            f"INSERT INTO test2 VALUES ({i}, {first_entry_ts + (i+1) * one_day})"
        )

    pds.query_data("CREATE TABLE _etl_bronze_test(id INT, timestamp INT64)")
    for i in range(5):
        pds.query_data(
            f"INSERT INTO _etl_bronze_test VALUES ({i}, {first_entry_ts + (i+1) * one_day})"
        )

    with patch("pdr_backend.cli.lake_cli.PersistentDataStore", return_value=pds):
        do_raw_drop(args)

    assert "drop table _temp_test1 starting at 1609459200000" in caplog.text
    assert "rows before: 5" in caplog.text
    assert "rows after: 2" in caplog.text
    assert "drop table test2 starting at 1609459200000" in caplog.text
    assert "rows before: 5" in caplog.text
    assert "rows after: 3" in caplog.text
    assert "skipping etl table _etl_bronze_test" in caplog.text
    assert "truncated 5 rows from 2 tables" in caplog.text


@enforce_types
def test_do_lake_raw_update(capsys):
    args = Namespace()
    args.ST = UnixTimeMs.from_timestr("2021-01-01")
    args.END = UnixTimeMs.from_timestr("2021-01-02")
    args.PPSS_FILE = "ppss.yaml"

    do_raw_update(args)
    assert (
        "TODO: start ms = 1609459200000, end ms = 1609545600000, ppss = ppss.yaml"
        in capsys.readouterr().out
    )


@enforce_types
def test_do_lake_etl_drop(tmpdir, caplog):
    args = Namespace()
    args.ST = UnixTimeMs.from_timestr("2021-01-01")  # 1609459200000
    args.LAKE_DIR = ""

    one_day = 1000 * 60 * 60 * 24
    first_entry_ts = 1609459200000 - one_day * 3  # 3 days before ST

    pds = PersistentDataStore(str(tmpdir))
    pds.query_data("CREATE TABLE _temp_bronze_test1 (id INT, timestamp INT64)")

    for i in range(5):
        pds.query_data(
            f"INSERT INTO _temp_bronze_test1 VALUES ({i}, {first_entry_ts + i * one_day})"
        )

    pds.query_data("CREATE TABLE _etl_silver_test2 (id INT, timestamp INT64)")

    for i in range(5):
        pds.query_data(
            f"INSERT INTO _etl_silver_test2 VALUES ({i}, {first_entry_ts + (i+1) * one_day})"
        )

    pds.query_data("CREATE TABLE _etl_test_raw(id INT, timestamp INT64)")
    for i in range(5):
        pds.query_data(
            f"INSERT INTO _etl_test_raw VALUES ({i}, {first_entry_ts + (i+1) * one_day})"
        )

    with patch("pdr_backend.cli.lake_cli.PersistentDataStore", return_value=pds):
        do_etl_drop(args)

    assert "drop table _temp_bronze_test1 starting at 1609459200000" in caplog.text
    assert "rows before: 5" in caplog.text
    assert "rows after: 2" in caplog.text
    assert "drop table _etl_silver_test2 starting at 1609459200000" in caplog.text
    assert "rows before: 5" in caplog.text
    assert "rows after: 3" in caplog.text
    assert "skipping non-etl table _etl_test_raw" in caplog.text
    assert "truncated 5 rows from 2 tables" in caplog.text


@enforce_types
def test_do_lake_etl_update(capsys):
    args = Namespace()
    args.ST = UnixTimeMs.from_timestr("2021-01-01")
    args.END = UnixTimeMs.from_timestr("2021-01-02")
    args.PPSS_FILE = "ppss.yaml"

    do_etl_update(args)
    assert (
        "TODO: start ms = 1609459200000, end ms = 1609545600000, ppss = ppss.yaml"
        in capsys.readouterr().out
    )
