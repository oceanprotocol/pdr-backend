from typing import List

from enforce_typing import enforce_types
import pytest

from pdr_backend.util.point_meta import PointMeta

@enforce_types
def test_point_meta_empty():
    pm = PointMeta({})
    assert pm.n_points() == 1
    assert pm.point_i(0) == {}
    assert "PointMeta" in str(pm)

    for bad_i in [-10, -1, 1, 10]:
        with pytest.raises(ValueError):
            _ = pm.point_i(bad_i)
    
@enforce_types
def test_point_meta_main():
    d = {
        "var1" : [10, 20],
        "var2" : ["a", "b"]
    }
    pm = PointMeta(d)
    
    target_ps = [
        {"var1": 10, "var2": "a"},
        {"var1": 10, "var2": "b"},
        {"var1": 20, "var2": "a"},
        {"var1": 20, "var2": "b"},
        ]

    assert sorted(pm.keys()) == ["var1", "var2"]
    assert pm["var1"] == [10, 20]

    s = str(pm)
    assert "PointMeta" in s
    assert "var1" in s
    assert "name=" in s
    assert "cand_vals" in s

    assert pm.n_points() == 4
    
    ps = [pm.point_i(i) for i in range(pm.n_points())]
    assert len(ps) == 4
    for target_p in target_ps:
        assert _dict_in_dictlist(target_p, ps)

    for bad_i in [-10, -1, 4, 10]:
        with pytest.raises(ValueError):
            _ = pm.point_i(bad_i)
            
    
def _dict_in_dictlist(d: dict, list_of_dicts: List[dict]) -> bool:
    """Return True if dict d is in list_of_dicts"""
    for dict_i in list_of_dicts:
        if d == dict_i:
            return True
    return False
