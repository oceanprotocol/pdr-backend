from unittest.mock import patch

from enforce_typing import enforce_types
import numpy as np
import polars as pl

from pdr_backend.predictoor.approach3.predictoor_agent3 import PredictoorAgent3
from pdr_backend.predictoor.test.predictoor_agent_runner import (
    run_agent_test,
    get_agent_1feed,
)


@enforce_types
def test_predictoor_agent3_main(tmpdir, monkeypatch):
    """
    @description
      Main end-to-end test of running agent 3.
    
      Runs the agent for a while, and then does some basic sanity checks.
    """
    run_agent_test(str(tmpdir), monkeypatch, PredictoorAgent3)


@enforce_types
@patch(
    "pdr_backend.predictoor.approach3.predictoor_agent3.PredictoorAgent3.get_data_components"
)
def test_predictoor_agent3_init(
    mock_get_data_components, tmpdir, monkeypatch
):
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

    
@enforce_types
def test_predictoor_agent3_get_prediction_1var(tmpdir, monkeypatch):
    """
    @description
      Test get_prediction(), when X has only 1 input variable

      Approach:
      - mergedohlcv_df has simple pre-set values: CLOSE_VALS
      - predprice = model.predict(X) is a simple sum of X-values
      - then, test that sum(CLOSE_VALS[-3:]) == predprice
    """
    CLOSE_VALS = [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.9, 19.0]
    def mock_get_data_components(*args, **kwargs):
        d = {
            # to check: timestamp may to align with predictoor_agent_runner.py:INIT_TIMESTAMP
            "timestamp": [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
            "binanceus:BTC/USDT:open" : [1.0] * 10,
            "binanceus:BTC/USDT:high" : [1.0] * 10,
            "binanceus:BTC/USDT:low" : [1.0] * 10,
            "binanceus:BTC/USDT:close" : CLOSE_VALS,
            "binanceus:BTC/USDT:volume" : [1.0] * 10,
        }
        mergedohlcv_df = pl.DataFrame(d)
        return mergedohlcv_df

    class MockModel:
        def __init__(self):
            self.aimodel_ss = None
            
        def predict(self, X: np.array):
            (n_points, n_vars) = X.shape
            assert n_points == 1 # this mock can only handle 1 input point
            assert self.aimodel_ss.n_feeds == 1 # 1 input feed
            assert n_vars == self.aimodel_ss.autoregressive_n * 1 
            assert n_vars == self.aimodel_ss.n # (1 feed) * autoregressive_n
            X_vals = X[0,-3:]
            y_val = sum(X_vals)
            return np.array([y_val])
    mock_model = MockModel()
        
    def mock_build(*args, **kwargs):
        return mock_model
    
    with patch("pdr_backend.predictoor.approach3.predictoor_agent3.PredictoorAgent3.get_data_components", mock_get_data_components), patch("pdr_backend.predictoor.approach3.predictoor_agent3.AimodelFactory.build", mock_build):
        # initialize agent
        _, ppss, agent, _ = \
            get_agent_1feed(str(tmpdir), monkeypatch, PredictoorAgent3)
        assert agent.last_predprice is None
        aimodel_ss = ppss.predictoor_ss.aimodel_ss
        assert aimodel_ss.n_feeds == 1 # 1 input feed
        mock_model.aimodel_ss = aimodel_ss

        timestamp = 5
        agent.get_prediction(timestamp)
        ar_n = aimodel_ss.autoregressive_n
        expected_X_vals = CLOSE_VALS[-ar_n:]
        expected_y_val = sum(expected_X_vals)
        assert agent.last_predprice == expected_y_val


@patch(
    "pdr_backend.predictoor.approach3.predictoor_agent3.PredictoorAgent3.get_data_components"
)
def test_predictoor_agent3_get_prediction_manyvars(
    mock_get_data_components, tmpdir, monkeypatch
):
    """
    @description
      Test get_prediction(), when X has only 1 input variable
    """
    pass
