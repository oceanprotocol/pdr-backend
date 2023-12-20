from pdr_backend.predictoor.approach1.predictoor_agent1 import PredictoorAgent1
from pdr_backend.predictoor.test.predictoor_agent_runner import run_agent_test


def test_predictoor_agent1(tmpdir, monkeypatch):
    run_agent_test(str(tmpdir), monkeypatch, PredictoorAgent1)
