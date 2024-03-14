from enforce_typing import enforce_types
import pytest

from pdr_backend.util.dictutil import dict_in_dictlist, keyval

@enforce_types
def test_dict_in_dictlist():
    assert not dict_in_dictlist({}, [])
    assert dict_in_dictlist({}, [{}])
    assert not dict_in_dictlist({"a": 1}, [])
    assert not dict_in_dictlist({}, [{"a": 1}])
    
    assert dict_in_dictlist({"a": 1}, [{"a": 1}])
    assert not dict_in_dictlist({"a": 1}, [{"b": 2}])
    
    assert dict_in_dictlist({"a": 1}, [{"a": 1}, {"b": 2}])
    assert dict_in_dictlist({"a": 1}, [{"b": 2}, {"a": 1}])

    assert not dict_in_dictlist({"b": 1}, [{"a": 1}])
    assert not dict_in_dictlist({"a": 2}, [{"a": 1}])
    

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
    
