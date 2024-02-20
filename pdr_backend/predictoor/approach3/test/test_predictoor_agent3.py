from unittest.mock import patch

from enforce_typing import enforce_types
import numpy as np
from numpy.testing import assert_array_equal
import polars as pl

from pdr_backend.predictoor.approach3.predictoor_agent3 import PredictoorAgent3
from pdr_backend.predictoor.test.predictoor_agent_runner import (
    run_agent_test,
    get_agent_1feed,
    get_agent_2feeds,
)
from pdr_backend.util.time_types import UnixTimeSeconds


# ===========================================================================
# test main loop


@enforce_types
def test_predictoor_agent3_main(tmpdir, monkeypatch):
    """
    @description
      Main end-to-end test of running agent 3.

      Runs the agent for a while, and then does some basic sanity checks.
    """
    run_agent_test(str(tmpdir), monkeypatch, PredictoorAgent3)


# ===========================================================================
# test __init__()


@enforce_types
@patch(
    "pdr_backend.predictoor.approach3.predictoor_agent3.PredictoorAgent3.get_data_components"
)
def test_predictoor_agent3_init(mock_get_data_components, tmpdir, monkeypatch):
    """
    @description
      Basic tests: is get_data_components() called? Is feed.name sane?
    """
    # initialize agent
    feed, _, _, _ = get_agent_1feed(str(tmpdir), monkeypatch, PredictoorAgent3)

    # assert get_data_components() is called once during init
    mock_get_data_components.assert_called_once()

    # assert agent was initialized with development feed
    assert "BTC/USDT|binanceus|5m" in feed.name


# ===========================================================================
# test get_prediction()

BTC_CLOSE_VALS = [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0]
ETH_CLOSE_VALS = [30.0, 31.0, 32.0, 33.0, 34.0, 35.0, 36.0, 37.0, 38.0, 39.0]


def mock_get_data_components2(*args, **kwargs):  # pylint: disable=unused-argument
    d = {
        "timestamp": [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
        "binanceus:BTC/USDT:open": [1.0] * 10,
        "binanceus:BTC/USDT:high": [1.0] * 10,
        "binanceus:BTC/USDT:low": [1.0] * 10,
        "binanceus:BTC/USDT:close": BTC_CLOSE_VALS,
        "binanceus:BTC/USDT:volume": [1.0] * 10,
        "binanceus:ETH/USDT:open": [1.0] * 10,
        "binanceus:ETH/USDT:high": [1.0] * 10,
        "binanceus:ETH/USDT:low": [1.0] * 10,
        "binanceus:ETH/USDT:close": ETH_CLOSE_VALS,
        "binanceus:ETH/USDT:volume": [1.0] * 10,
    }
    mergedohlcv_df = pl.DataFrame(d)
    return mergedohlcv_df


class MockModel:
    """scikit-learn style model"""

    def __init__(self):
        self.aimodel_ss = None  # fill this in later, after patch applied
        self.last_X = None  # for tracking test results
        self.last_y = None  # ""

    def predict(self, X: np.ndarray) -> np.ndarray:
        ar_n = self.aimodel_ss.autoregressive_n
        n_feeds = self.aimodel_ss.n_feeds
        (n_points, n_vars) = X.shape
        assert n_points == 1  # this mock can only handle 1 input point
        assert n_vars == self.aimodel_ss.n == ar_n * n_feeds
        yval: float = np.sum(X)
        y: np.ndarray = np.array([yval])
        self.last_X, self.last_y = X, y  # cache for testing
        return y


@enforce_types
def test_predictoor_agent3_get_prediction_1feed(tmpdir, monkeypatch):
    """
    @description
      Test get_prediction(), when X has only 1 input feed

      Approach:
      - mergedohlcv_df has simple pre-set values: CLOSE_VALS
      - predprice = model.predict(X) is a simple sum of X-values
      - then, test that sum(CLOSE_VALS[-ar_n:]) == predprice
        where ar_n = autoregressive_n = 3
    """
    mock_model = MockModel()

    def mock_build(*args, **kwargs):  # pylint: disable=unused-argument
        return mock_model

    with patch(
        "pdr_backend.predictoor.approach3.predictoor_agent3.PredictoorAgent3.get_data_components",
        mock_get_data_components2,
    ), patch(
        "pdr_backend.predictoor.approach3.predictoor_agent3.AimodelFactory.build",
        mock_build,
    ):

        # initialize agent
        _, ppss, agent, _ = get_agent_1feed(str(tmpdir), monkeypatch, PredictoorAgent3)
        aimodel_ss = ppss.predictoor_ss.aimodel_ss
        assert aimodel_ss.n_feeds == 1

        # do prediction
        mock_model.aimodel_ss = aimodel_ss
        agent.get_prediction(timestamp=UnixTimeSeconds(5))  # arbitrary timestamp

        ar_n = aimodel_ss.autoregressive_n
        assert ar_n == 3

        assert mock_model.last_X.shape == (1, 3) == (1, ar_n * 1)
        expected_X = np.array([BTC_CLOSE_VALS[-ar_n:]])  # [17.0, 18.0, 19.0]
        expected_yval = sum(BTC_CLOSE_VALS[-ar_n:])
        expected_y = np.array([expected_yval])

        assert_array_equal(expected_X, mock_model.last_X)
        assert_array_equal(expected_y, mock_model.last_y)


@enforce_types
def test_predictoor_agent3_get_prediction_2feeds(tmpdir, monkeypatch):
    """
    @description
      Test get_prediction(), when X has >1 input feed
    """
    mock_model = MockModel()

    def mock_build(*args, **kwargs):  # pylint: disable=unused-argument
        return mock_model

    with patch(
        "pdr_backend.predictoor.approach3.predictoor_agent3.PredictoorAgent3.get_data_components",
        mock_get_data_components2,
    ), patch(
        "pdr_backend.predictoor.approach3.predictoor_agent3.AimodelFactory.build",
        mock_build,
    ):

        # initialize agent
        feeds, ppss, agent = get_agent_2feeds(
            str(tmpdir), monkeypatch, PredictoorAgent3
        )
        assert len(feeds) == 2
        aimodel_ss = ppss.predictoor_ss.aimodel_ss
        assert aimodel_ss.n_feeds == 2

        # do prediction
        mock_model.aimodel_ss = aimodel_ss
        agent.get_prediction(timestamp=UnixTimeSeconds(5))  # arbitrary timestamp

        ar_n = aimodel_ss.autoregressive_n
        assert ar_n == 3

        assert mock_model.last_X.shape == (1, 6) == (1, ar_n * 2)
        # [17.0, 18.0, 19.0, 37.0, 38.0, 39.0]
        expected_X = np.array([BTC_CLOSE_VALS[-ar_n:] + ETH_CLOSE_VALS[-ar_n:]])
        expected_yval = sum(BTC_CLOSE_VALS[-ar_n:] + ETH_CLOSE_VALS[-ar_n:])
        expected_y = np.array([expected_yval])

        assert_array_equal(expected_X, mock_model.last_X)
        assert_array_equal(expected_y, mock_model.last_y)
