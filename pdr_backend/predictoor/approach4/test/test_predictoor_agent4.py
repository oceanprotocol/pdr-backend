from unittest.mock import patch

from pdr_backend.predictoor.approach4.predictoor_agent4 import PredictoorAgent4
from pdr_backend.predictoor.test.predictoor_agent_runner import (
    run_agent_test,
    get_agent,
)


def test_predictoor_agent4(tmpdir, monkeypatch):
    run_agent_test(str(tmpdir), monkeypatch, PredictoorAgent4)


@patch(
    "pdr_backend.predictoor.approach4.predictoor_agent4.PredictoorAgent4.get_data_components"
)
def test_predictoor_agent4_data_component(
    mock_get_data_components, tmpdir, monkeypatch
):
    """
    @description
        Test that PredictoorAgent4.get_data_components() is called once.
    """
    # initialize agent
    feed, _, _, _ = get_agent(str(tmpdir), monkeypatch, PredictoorAgent4)

    # assert get_data_components() is called once during init
    mock_get_data_components.assert_called_once()

    # assert agent was initialized with development feed
    assert "BTC/USDT|binanceus|5m" in feed.name
