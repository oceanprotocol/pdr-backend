from enforce_typing import enforce_types
import pytest

from pdr_backend.util.dictutil import keyval


@enforce_types
def test_keyval():
    assert keyval({"thekey": "theval"}) == ("thekey", "theval")

    with pytest.raises(TypeError):
        _ = keyval("not a dict")
    with pytest.raises(TypeError):
        _ = keyval(["not a dict"])
    with pytest.raises(ValueError):
        _ = keyval({})
    with pytest.raises(ValueError):
        _ = keyval({"thekey": "theval", "key2": "val2"})
    
