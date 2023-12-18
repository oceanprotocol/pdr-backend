from pdr_backend.predictoor.test.predictoor_agent_runner import run_agent_test
from pdr_backend.predictoor.approach3.predictoor_agent3 import PredictoorAgent3


def test_predictoor_agent3(tmpdir, monkeypatch):
    run_agent_test(str(tmpdir), monkeypatch, PredictoorAgent3)
