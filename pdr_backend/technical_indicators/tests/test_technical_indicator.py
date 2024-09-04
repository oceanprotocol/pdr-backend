import pytest
import pandas as pd
import pandas as pd

from pdr_backend.technical_indicators.technical_indicator import (
    MockTechnicalIndicator,
    TechnicalIndicator,
)


def test_mock_technical_indicator(sample_df):
    indicator = MockTechnicalIndicator(
        df=sample_df,
        open_col="open",
        high_col="high",
        low_col="low",
        close_col="close",
        volume_col="volume",
    )

    assert indicator._open().equals(sample_df["open"])
    assert indicator._high().equals(sample_df["high"])
    assert indicator._low().equals(sample_df["low"])
    assert indicator._close().equals(sample_df["close"])
    assert indicator._volume().equals(sample_df["volume"])

    expected_result = sample_df["close"] * 0.5
    pd.testing.assert_series_equal(indicator.calculate(), expected_result)


def test_abstract_method_implementation():
    with pytest.raises(TypeError):
        TechnicalIndicator(
            df=pd.DataFrame(),
            open_col="open",
            high_col="high",
            low_col="low",
            close_col="close",
            volume_col="volume",
        )
