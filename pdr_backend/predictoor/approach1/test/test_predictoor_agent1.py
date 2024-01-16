from unittest.mock import MagicMock

import pytest
from enforce_typing import enforce_types

from pdr_backend.ppss.ppss import PPSS
from pdr_backend.ppss.predictoor_ss import PredictoorSS
from pdr_backend.ppss.web3_pp import Web3PP
from pdr_backend.predictoor.approach1.predictoor_agent1 import PredictoorAgent1
from pdr_backend.predictoor.test.predictoor_agent_runner import run_agent_test


def test_predictoor_agent1(tmpdir, monkeypatch):
    run_agent_test(str(tmpdir), monkeypatch, PredictoorAgent1)


def test_run():
    mock_predictoor_agent1 = MagicMock(spec=PredictoorAgent1)
    take_step = mock_predictoor_agent1.take_step
    take_step.return_value = None

    mock_predictoor_agent1.run()


@enforce_types
def test_agent_constructor_empty():
    # test with no feeds
    mock_ppss_empty = MagicMock(spec=PPSS)
    mock_ppss_empty.predictoor_ss = MagicMock(spec=PredictoorSS)
    mock_ppss_empty.predictoor_ss.get_feed_from_candidates.return_value = None
    mock_ppss_empty.web3_pp = MagicMock(spec=Web3PP)
    mock_ppss_empty.web3_pp.query_feed_contracts.return_value = {}

    with pytest.raises(ValueError, match="No feeds found"):
        PredictoorAgent1(mock_ppss_empty)
