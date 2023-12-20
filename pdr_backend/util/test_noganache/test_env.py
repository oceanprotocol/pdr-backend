import pytest
from enforce_typing import enforce_types

from pdr_backend.util.env import getenv_or_exit


@enforce_types
def test_getenv_or_exit(monkeypatch):
    monkeypatch.delenv("MY_VAR", raising=False)
    with pytest.raises(SystemExit):
        getenv_or_exit("MY_VAR")

    monkeypatch.setenv("MY_VAR", "http://test.url")
    assert getenv_or_exit("MY_VAR") == "http://test.url"
