from argparse import Namespace
from unittest.mock import Mock, patch

# import pytest
from enforce_typing import enforce_types

from pdr_backend.cli.cli_module_lake import (
    DuckDBDataStore,
    do_lake_describe,
    do_lake_etl_drop,
    #    do_lake_etl_update,
    do_lake_query,
    do_lake_raw_drop,
    do_lake_raw_update,
    do_lake_subcommand,
    do_lake_validate,
)
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.util.time_types import UnixTimeMs


@enforce_types
def test_do_lake_subcommand():
    with patch(
        "pdr_backend.cli.cli_module_lake.do_lake_describe"
    ) as mock_do_lake_describe:
        do_lake_subcommand(["describe", "ppss.yaml", "sapphire-mainnet"])

    mock_do_lake_describe.assert_called_once()

    with patch("pdr_backend.cli.cli_module_lake.do_lake_query") as mock_do_lake_query:
        do_lake_subcommand(["query", "ppss.yaml", "sapphire-mainnet", "query"])

    mock_do_lake_query.assert_called_once()


@enforce_types
def test_do_lake_describe():
    args = Namespace()
    args.subcommand = "describe"
    args.PPSS_FILE = "ppss.yaml"
    args.NETWORK = "sapphire-mainnet"
    args.HTML = False

    ppss = Mock()

    with patch("pdr_backend.cli.cli_module_lake.LakeInfo") as mock_lake_info:
        do_lake_describe(args, ppss)

    mock_lake_info.assert_called_once_with(ppss, use_html=False)


@enforce_types
def test_do_lake_validate():
    args = Namespace()
    args.subcommand = "validate"
    args.PPSS_FILE = "ppss.yaml"
    args.NETWORK = "sapphire-mainnet"

    ppss = Mock()

    with patch("pdr_backend.cli.cli_module_lake.LakeValidate") as mock_lake_info:
        do_lake_validate(args, ppss)

    mock_lake_info.assert_called_once_with(ppss)


@enforce_types
def test_do_lake_query(caplog):
    query = "SELECT * FROM table"

    args = Namespace()
    args.QUERY = query
    args.PPSS_FILE = "ppss.yaml"
    args.NETWORK = "sapphire-mainnet"

    mock_pds = Mock()
    mock_pds.query_data.return_value = "query result"
    mock_ppss = Mock()

    with patch(
        "pdr_backend.cli.cli_module_lake.DuckDBDataStore", return_value=mock_pds
    ):
        do_lake_query(args, mock_ppss)

    mock_pds.query_data.assert_called_once_with(query)

    mock_pds_err = Mock()
    mock_pds_err.query_data.side_effect = Exception("boom!")

    with patch(
        "pdr_backend.cli.cli_module_lake.DuckDBDataStore", return_value=mock_pds_err
    ):
        do_lake_query(args, mock_ppss)

    assert "Error querying lake: boom!" in caplog.text


@enforce_types
def test_do_lake_raw_delegation():
    args = ["raw", "drop", "ppss.yaml", "sapphire-mainnet", "2021-01-01"]

    with patch("pdr_backend.cli.cli_module_lake.do_lake_raw_drop") as raw_drop:
        do_lake_subcommand(args)

    assert raw_drop.called

    args = ["raw", "update", "ppss.yaml", "sapphire-mainnet"]

    with patch("pdr_backend.cli.cli_module_lake.do_lake_raw_update") as raw_update:
        do_lake_subcommand(args)

    assert raw_update.called


# @enforce_types
# def test_do_lake_etl_delegation():
#     args = ["etl", "drop", "ppss.yaml", "sapphire-mainnet", "2021-01-01"]

#     with patch("pdr_backend.cli.cli_module_lake.do_lake_etl_drop") as etl_drop:
#         do_lake_subcommand(args)

#     assert etl_drop.called
#     assert isinstance(etl_drop.call_args[0][0].ST, UnixTimeMs)

#     args.append("2021-01-01")
#     with pytest.raises(SystemExit):
#         # raw does not recognize the extra END argument
#         do_lake_subcommand(args)

#     args = ["etl", "update", "ppss.yaml", "sapphire-mainnet"]

#     with patch("pdr_backend.cli.cli_module_lake.do_lake_etl_update") as etl_update:
#         do_lake_subcommand(args)

#     assert etl_update.called


def _make_and_fill_timestamps(db, table_name, first_entry_ts):
    one_day = 1000 * 60 * 60 * 24
    db.query_data(f"CREATE TABLE {table_name} (id INT, timestamp INT64)")

    for i in range(5):
        db.query_data(
            f"INSERT INTO {table_name} VALUES ({i}, {first_entry_ts + i * one_day})"
        )


@enforce_types
def test_do_lake_raw_drop(tmpdir, caplog):
    args = Namespace()
    args.ST = UnixTimeMs.from_timestr("2021-01-01")  # 1609459200000
    args.LAKE_DIR = ""
    args.PPSS_FILE = "ppss.yaml"
    args.NETWORK = "sapphire-mainnet"

    ts = 1609459200000
    one_day = 1000 * 60 * 60 * 24

    db = DuckDBDataStore(str(tmpdir))
    _make_and_fill_timestamps(db, "_temp_test1", ts - 3 * one_day)
    _make_and_fill_timestamps(db, "test2", ts - 2 * one_day)
    _make_and_fill_timestamps(db, "_etl_bronze_test", ts - 2 * one_day)

    mock_ppss = Mock()

    with patch("pdr_backend.cli.cli_module_lake.DuckDBDataStore", return_value=db):
        do_lake_raw_drop(args, mock_ppss)

    assert "drop table _temp_test1 starting at 1609459200000" in caplog.text
    assert "rows before: 5" in caplog.text
    assert "rows after: 2" in caplog.text
    assert "drop table test2 starting at 1609459200000" in caplog.text
    assert "rows before: 5" in caplog.text
    assert "rows after: 3" in caplog.text
    assert "truncated 5 rows from 2 tables" in caplog.text


@enforce_types
def test_do_lake_etl_drop(tmpdir, caplog):
    args = Namespace()
    args.ST = UnixTimeMs.from_timestr("2021-01-01")  # 1609459200000
    args.LAKE_DIR = ""
    args.PPSS_FILE = "ppss.yaml"
    args.NETWORK = "sapphire-mainnet"

    one_day = 1000 * 60 * 60 * 24
    ts = 1609459200000

    db = DuckDBDataStore(str(tmpdir))
    _make_and_fill_timestamps(db, "_temp_bronze_test1", ts - 3 * one_day)
    _make_and_fill_timestamps(db, "_etl_silver_test2", ts - 2 * one_day)
    _make_and_fill_timestamps(db, "_etl_test_raw", ts - 2 * one_day)

    mock_ppss = Mock()

    with patch("pdr_backend.cli.cli_module_lake.DuckDBDataStore", return_value=db):
        do_lake_etl_drop(args, mock_ppss)

    assert "drop table _temp_bronze_test1 starting at 1609459200000" in caplog.text
    assert "rows before: 5" in caplog.text
    assert "rows after: 2" in caplog.text
    assert "drop table _etl_silver_test2 starting at 1609459200000" in caplog.text
    assert "rows before: 5" in caplog.text
    assert "rows after: 3" in caplog.text
    assert "skipping non-etl table _etl_test_raw" in caplog.text
    assert "truncated 5 rows from 2 tables" in caplog.text


@enforce_types
def test_do_lake_raw_update(capsys):
    args = Namespace()
    ppss = Mock(spec=PPSS)

    with patch("pdr_backend.cli.cli_module_lake.GQLDataFactory"):
        do_lake_raw_update(args, ppss)

    assert capsys.readouterr().out == ""


#
# @enforce_types
# def test_do_lake_etl_update(capsys):
#     args = Namespace()
#     ppss = Mock(spec=PPSS)
#
#     with patch("pdr_backend.cli.cli_module_lake.GQLDataFactory"):
#         with patch("pdr_backend.cli.cli_module_lake.ETL"):
#             do_lake_etl_update(args, ppss)
#
#     assert capsys.readouterr().out == ""
