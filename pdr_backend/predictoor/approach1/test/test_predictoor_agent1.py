from pdr_backend.predictoor.test.agent_runner import run_agent_test
from pdr_backend.predictoor.approach1.predictoor_agent1 import PredictoorAgent1


def test_predictoor_agent1(tmpdir, monkeypatch):
    run_agent_test(tmpdir, monkeypatch, PredictoorAgent1)
