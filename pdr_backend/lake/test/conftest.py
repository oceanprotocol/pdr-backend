import pytest

from pdr_backend.models.prediction import mock_daily_predictions
from pdr_backend.lake.plutil import text_to_df


@pytest.fixture()
def sample_daily_predictions():
    return mock_daily_predictions()


# ==================================================================


@pytest.fixture()
def raw_df1():  # binance BTC/USDT
    return text_to_df(
        """datetime|timestamp|open|close
d0|0|10.0|11.0
d1|1|10.1|11.1
d3|3|10.3|11.3
d4|4|10.4|11.4
"""
    )  # does not have: "d2|2|10.2|11.2" to simulate missing vals from exchanges


@pytest.fixture()
def raw_df2():  # binance ETH/USDT
    return text_to_df(
        """datetime|timestamp|open|close
d0|0|20.0|21.0
d1|1|20.1|21.1
d2|2|20.2|21.2
d3|3|20.3|21.3
"""
    )  # does *not* have: "d4|4|20.4|21.4" to simulate missing vals from exchanges


# ==================================================================@pytest.fixture()
def raw_df3():  # kraken BTC/USDT
    return text_to_df(
        """datetime|timestamp|open|close
d0|0|30.0|31.0
d1|1|30.1|31.1
d2|2|30.2|31.2
d3|3|30.3|31.3
d4|4|30.4|31.4
"""
    )


@pytest.fixture()
def raw_df4():  # kraken ETH/USDT
    return text_to_df(
        """datetime|timestamp|open|close
d0|0|40.0|41.0
d1|1|40.1|41.1
d2|2|40.2|41.2
d3|3|40.3|41.3
d4|4|40.4|41.4
"""
    )
