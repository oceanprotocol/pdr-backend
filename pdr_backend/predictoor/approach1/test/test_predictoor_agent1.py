from unittest.mock import MagicMock

import pytest
from enforce_typing import enforce_types

from pdr_backend.ppss.ppss import PPSS
from pdr_backend.ppss.predictoor_ss import PredictoorSS
from pdr_backend.ppss.web3_pp import Web3PP
from pdr_backend.predictoor.approach1.predictoor_agent1 import PredictoorAgent1
from pdr_backend.predictoor.test.predictoor_agent_runner import run_agent_test


@enforce_types
def test_predictoor_agent1_main(tmpdir, monkeypatch):
    """
    @description
      Main end-to-end test of running agent 1.
    
      Runs the agent for a while, and then does some basic sanity checks.
    """
    run_agent_test(str(tmpdir), monkeypatch, PredictoorAgent1)


@enforce_types
def test_predictoor_agent1_run():
    """
    @description
      Another end-to-end test of running agent 1.
    
      Runs the agent for 1 iteration, then stops because envvar TEST == true.
    """
    mock_predictoor_agent1 = MagicMock(spec=PredictoorAgent1)
    take_step = mock_predictoor_agent1.take_step
    take_step.return_value = None

    mock_predictoor_agent1.run()


@enforce_types
def test_agent_init_empty():
    """
    @description
      Basic test: when there's no feeds, does it complain?
    """
    # test with no feeds
    mock_ppss_empty = MagicMock(spec=PPSS)
    mock_ppss_empty.predictoor_ss = MagicMock(spec=PredictoorSS)
    mock_ppss_empty.predictoor_ss.get_feed_from_candidates.return_value = None
    mock_ppss_empty.web3_pp = MagicMock(spec=Web3PP)
    mock_ppss_empty.web3_pp.query_feed_contracts.return_value = {}

    with pytest.raises(ValueError, match="No feeds found"):
        PredictoorAgent1(mock_ppss_empty)
