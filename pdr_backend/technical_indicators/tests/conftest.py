import pandas as pd
import pytest


@pytest.fixture
def sample_df():
    data = {
        "open": [1.0, 2.0, 3.0, 4.0, 5.0],
        "high": [1.5, 2.5, 3.5, 4.5, 5.5],
        "low": [0.5, 1.5, 2.5, 3.5, 4.5],
        "close": [1.2, 2.2, 3.2, 4.2, 5.2],
        "volume": [1000, 1500, 2000, 2500, 3000],
    }
    return pd.DataFrame(data)
