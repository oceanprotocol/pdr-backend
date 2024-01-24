import pytest
from unittest.mock import patch
from enforce_typing import enforce_types
import polars as pl

from pdr_backend.lake.test.resources import (
    _etl_instance,)

@enforce_types
@patch("pdr_backend.lake.etl.pl.read_parquet")
def test_read(
    mock_read_parquet,
    tmpdir
    ):
    mock_read_parquet.return_value = pl.DataFrame(data={"a": [1, 2, 3]})

    etl_instance = _etl_instance(tmpdir)
    result = etl_instance.read("payouts")

    assert result["a"][0] == 1
    assert result["a"][1] == 2
    assert result["a"][2] == 3
    mock_read_parquet.assert_called_once_with(
        f"{tmpdir}/pdr_payouts.parquet"
    )

@enforce_types
def test_post_fetch_processing_invalid_fp_type(tmpdir):
    etl_instance = _etl_instance(tmpdir)
    with pytest.raises(ValueError):
        etl_instance.post_fetch_processing("invalid", 0, 0, {})

@enforce_types
@patch("pdr_backend.lake.etl.ETL._post_fetch_processing_payout")
def test_post_fetch_processing_with_valid_fp_type(
    mock_post_fetch_processing_payout,
    tmpdir
):
    mock_post_fetch_processing_payout.return_value = None

    etl_instance = _etl_instance(tmpdir)
    etl_instance.post_fetch_processing("payout", 1, 2, {})
    mock_post_fetch_processing_payout.assert_called_once_with(1, 2, {})
