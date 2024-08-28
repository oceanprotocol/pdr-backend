import pytest
import pandas as pd
from pdr_backend.lake.alt_bar import (
    _extract_bars,
    get_dollar_bars,
    get_volume_bars,
    get_tick_bars,
)


@pytest.fixture(name="sample_data")
def fixture_sample_data():
    data = {
        "timestamp": pd.date_range(start="2024-01-01", periods=5, freq="min"),
        "open": [100, 101, 102, 103, 104],
        "high": [101, 102, 103, 104, 105],
        "low": [99, 100, 101, 102, 103],
        "close": [100.5, 101.5, 102.5, 103.5, 104.5],
        "volume": [1000, 1500, 2000, 2500, 3000],
    }
    df = pd.DataFrame(data)
    return df.sort_values(by="timestamp", ascending=True)


def test_extract_bars_dollar_metric(sample_data):
    bars, start_tm = _extract_bars(
        sample_data, metric="cum_dollar_value", threshold=1000000
    )
    assert len(bars) == 1
    assert start_tm == sample_data.iloc[4, 0]
    assert bars[0][5] == sum(sample_data["volume"])


def test_extract_bars_volume_metric(sample_data):
    bars, start_tm = _extract_bars(sample_data, metric="cum_volume", threshold=4000)
    assert len(bars) == 2
    assert start_tm == sample_data.iloc[4, 0]
    assert bars[0][5] == float(4500)
    assert bars[1][5] == float(5500)


def test_extract_bars_tick_metric(sample_data):
    bars, start_tm = _extract_bars(sample_data, metric="cum_ticks", threshold=3)
    assert len(bars) == 1
    assert start_tm == sample_data.iloc[2, 0]
    assert bars[0][7] == 3


def test_get_dollar_bars(sample_data):
    bars, start_tm = get_dollar_bars(sample_data, threshold=1000000)
    assert len(bars) == 1
    assert start_tm == sample_data.iloc[4, 0]
    assert bars[0][5] == sum(sample_data["volume"])


def test_get_volume_bars(sample_data):
    bars, start_tm = get_volume_bars(sample_data, threshold=4000)
    assert len(bars) == 2
    assert start_tm == sample_data.iloc[4, 0]
    assert bars[0][5] == float(4500)
    assert bars[1][5] == float(5500)


def test_get_tick_bars(sample_data):
    bars, start_tm = get_tick_bars(sample_data, threshold=3)
    assert len(bars) == 1
    assert start_tm == sample_data.iloc[2, 0]
    assert bars[0][7] == 3
