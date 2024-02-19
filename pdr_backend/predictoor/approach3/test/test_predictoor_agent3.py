from unittest.mock import patch

from enforce_typing import enforce_types

from pdr_backend.predictoor.approach3.predictoor_agent3 import PredictoorAgent3
from pdr_backend.predictoor.test.predictoor_agent_runner import (
    run_agent_test,
    get_agent,
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
    feed, _, _, _ = get_agent(str(tmpdir), monkeypatch, PredictoorAgent3)

    # assert get_data_components() is called once during init
    mock_get_data_components.assert_called_once()

    # assert agent was initialized with development feed
    assert "BTC/USDT|binanceus|5m" in feed.name

    
@enforce_types
@patch(
    "pdr_backend.predictoor.approach3.predictoor_agent3.PredictoorAgent3.get_data_components"
)
def test_predictoor_agent3_get_prediction_1var_input(
    mock_get_data_components, tmpdir, monkeypatch
):
    """
    @description
      Test get_prediction(), when X has only 1 input variable
    """
    # FIXME: have a proper mock of get_data_components

    # FIXME: have a proper mock of AimodelFactory, where the output is
    # a simple obvious function of input values, e.g. sum(input values)
    
    # initialize agent
    feed, ppss, agent, _mock_pdr_contract = \
        get_agent(str(tmpdir), monkeypatch, PredictoorAgent3)


    #timestamp = 0 # FIXME
    #(predval, stake) = agent.get_prediction(timestamp)

    # FIXME test predval: is it the simple obvious function of input values?


@patch(
    "pdr_backend.predictoor.approach3.predictoor_agent3.PredictoorAgent3.get_data_components"
)
def test_predictoor_agent3_get_prediction_manyvars_input(
    mock_get_data_components, tmpdir, monkeypatch
):
    """
    @description
      Test get_prediction(), when X has only 1 input variable
    """
    pass
