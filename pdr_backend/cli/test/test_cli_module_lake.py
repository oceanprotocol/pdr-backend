import os
from argparse import Namespace
from unittest.mock import Mock, patch

import pytest
from enforce_typing import enforce_types

from pdr_backend.cli.cli_module_lake import (
    PersistentDataStore,
    do_lake_describe,
    do_lake_drop,
    do_lake_update,
    do_lake_query,
    do_lake_subcommand,
)
from pdr_backend.util.time_types import UnixTimeMs


@enforce_types
def test_do_lake_subcommand():
    with patch(
        "pdr_backend.cli.cli_module_lake.do_lake_describe"
    ) as mock_do_lake_describe:
        do_lake_subcommand(["describe", "lake_data"])

    mock_do_lake_describe.assert_called_once()

    with patch("pdr_backend.cli.cli_module_lake.do_lake_query") as mock_do_lake_query:
        do_lake_subcommand(["query", "lake_data", "query"])

    mock_do_lake_query.assert_called_once()


@enforce_types
def test_do_lake_describe():
    lake_dir = os.path.abspath("lake_data")
    args = Namespace()
    args.subcommand = "describe"
    args.LAKE_DIR = lake_dir

    with patch("pdr_backend.cli.cli_module_lake.LakeInfo") as mock_lake_info:
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

    with patch(
        "pdr_backend.cli.cli_module_lake.PersistentDataStore", return_value=mock_pds
    ):
        do_lake_query(args)

    mock_pds.query_data.assert_called_once_with(query)

    mock_pds_err = Mock()
    mock_pds_err.query_data.side_effect = Exception("boom!")

    with patch(
        "pdr_backend.cli.cli_module_lake.PersistentDataStore", return_value=mock_pds_err
    ):
        do_lake_query(args)

    assert "Error querying lake: boom!" in caplog.text


@enforce_types
def test_do_lake_delegation():
    args = ["drop", "lake_data", "2021-01-01"]

    with patch("pdr_backend.cli.cli_module_lake.do_lake_drop") as lake_drop:
        do_lake_subcommand(args)

    assert lake_drop.called
    assert isinstance(lake_drop.call_args[0][0].ST, UnixTimeMs)

    args.append("2021-01-01")
    with pytest.raises(SystemExit):
        # raw does not recognize the extra END argument
        do_lake_subcommand(args)

    args = [
        "update",
        "ppss.yaml",
        "sapphire-mainnet",
        "2021-01-01",
        "2021-01-02",
    ]

    with patch("pdr_backend.cli.cli_module_lake.do_lake_update") as lake_update:
        do_lake_subcommand(args)

    assert lake_update.called


def _make_and_fill_timestamps(pds, table_name, first_entry_ts):
    one_day = 1000 * 60 * 60 * 24
    pds.query_data(f"CREATE TABLE {table_name} (id INT, timestamp INT64)")

    for i in range(5):
        pds.query_data(
            f"INSERT INTO {table_name} VALUES ({i}, {first_entry_ts + i * one_day})"
        )


@enforce_types
def test_do_lake_drop(tmpdir, caplog):
    args = Namespace()
    args.ST = UnixTimeMs.from_timestr("2021-01-01")  # 1609459200000
    args.LAKE_DIR = ""

    ts = 1609459200000
    one_day = 1000 * 60 * 60 * 24

    pds = PersistentDataStore(str(tmpdir))
    _make_and_fill_timestamps(pds, "_temp_test1", ts - 3 * one_day)
    _make_and_fill_timestamps(pds, "test2", ts - 2 * one_day)
    _make_and_fill_timestamps(pds, "_etl_bronze_test", ts - 2 * one_day)

    with patch("pdr_backend.cli.cli_module_lake.PersistentDataStore", return_value=pds):
        do_lake_drop(args)

    assert "drop table _temp_test1 starting at 1609459200000" in caplog.text
    assert "rows before: 5" in caplog.text
    assert "rows after: 2" in caplog.text
    assert "drop table test2 starting at 1609459200000" in caplog.text
    assert "rows before: 5" in caplog.text
    assert "rows after: 3" in caplog.text
    assert "truncated 8 rows from 3 tables" in caplog.text


@enforce_types
def test_do_lake_update(capsys):
    args = Namespace()
    args.ST = UnixTimeMs.from_timestr("2021-01-01")
    args.END = UnixTimeMs.from_timestr("2021-01-02")
    args.PPSS_FILE = "ppss.yaml"

    do_lake_update(args)
    assert (
        "TODO: start ms = 1609459200000, end ms = 1609545600000, ppss = ppss.yaml"
        in capsys.readouterr().out
    )
