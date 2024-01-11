from unittest.mock import patch

from pdr_backend.predictoor.approach3.predictoor_agent3 import PredictoorAgent3
from pdr_backend.predictoor.test.predictoor_agent_runner import (
    run_agent_test,
    get_agent,
)
from pdr_backend.ppss.web3_pp import del_network_override


def test_predictoor_agent3(tmpdir, monkeypatch):
    run_agent_test(str(tmpdir), monkeypatch, PredictoorAgent3)


@patch(
    "pdr_backend.predictoor.approach3.predictoor_agent3.PredictoorAgent3.get_data_components"
)
def test_predictoor_agent3_data_component(
    mock_get_data_components, tmpdir, monkeypatch
):
    """
    @description
        Test that PredictoorAgent3.get_data_components() is called once.
    """
    del_network_override(monkeypatch)

    # initialize agent
    feed, _, _, _ = get_agent(str(tmpdir), monkeypatch, PredictoorAgent3)

    # assert get_data_components() is called once during init
    mock_get_data_components.assert_called_once()

    # assert agent was initialized with development feed
    assert "BTC/USDT|binanceus|5m" in feed.name
