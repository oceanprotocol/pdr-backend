import os
from argparse import Namespace
from unittest.mock import Mock, patch

from enforce_typing import enforce_types

from pdr_backend.cli.lake_cli import (
    do_lake_describe,
    do_lake_query,
    do_lake_subcommand,
    get_lake_dir,
)


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
