import pytest

from pdr_backend.utils.env import getenv_or_exit


def test_getenv_or_exit(monkeypatch):
    monkeypatch.delenv("RPC_URL", raising=False)
    with pytest.raises(SystemExit):
        getenv_or_exit("RPC_URL")

    monkeypatch.setenv("RPC_URL", "http://test.url")
    assert getenv_or_exit("RPC_URL") == "http://test.url"
