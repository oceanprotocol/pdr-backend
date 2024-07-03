import io
from unittest.mock import MagicMock

import polars as pl
from enforce_typing import enforce_types

from pdr_backend.lake_info.overview import TableViewsOverview, ValidationOverview
from pdr_backend.lake_info.test.resources import csv_string


@enforce_types
def test_validate_lake_mock_sql_failure():
    sql_result = pl.read_csv(io.StringIO(csv_string))
    assert isinstance(sql_result, pl.DataFrame)

    mock_pds = MagicMock()
    mock_pds.query_data.return_value = sql_result
    mock_pds.get_table_names.return_value = ["table1", "table2"]
    mock_pds.get_view_names.return_value = ["view1", "view2"]

    validation_overview = ValidationOverview(mock_pds)
    result = validation_overview.validate_lake_bronze_predictions_gaps()

    # assert that the function called the query_data method
    mock_pds.query_data.assert_called()

    # assert that the data validation failed as we would expect it to
    # review the logs and verify the data is what we expect to see
    assert isinstance(result, list)
    assert len(result) == 0

    result = validation_overview.validate_expected_table_names()
    assert isinstance(result, list)
    assert len(result) == 0

    result = validation_overview.validate_expected_view_names()
    assert isinstance(result, list)
    assert len(result) == 2
    assert "Unexpected view: view1. Please clean using CLI." in result

    result = validation_overview.validate_lake_tables_no_duplicates()
    assert isinstance(result, list)
    assert len(result) == 2
    assert "Table table1 has duplicates." in result

    table_overview = TableViewsOverview(mock_pds)
    assert table_overview.all_table_names == ["table1", "table2"]
    assert table_overview.all_view_names == ["view1", "view2"]
