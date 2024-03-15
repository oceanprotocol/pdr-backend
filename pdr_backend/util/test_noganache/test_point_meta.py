from collections import OrderedDict
from typing import List

from enforce_typing import enforce_types
import pytest

from pdr_backend.util.listutil import obj_in_objlist
from pdr_backend.util.point import Point
from pdr_backend.util.point_meta import PointMeta


@enforce_types
def test_point_meta_empty():
    pm = PointMeta()
    assert pm.n_points == 1
    assert pm.point_i(0) == Point()
    assert "PointMeta" in str(pm)

    for bad_i in [-10, -1, 1, 10]:
        with pytest.raises(ValueError):
            _ = pm.point_i(bad_i)


@enforce_types
def test_point_meta_main():
    pm = PointMeta([("var1", [10, 20]), ("var2", ["a", "b"])])

    target_ps = [
        Point([("var1", 10), ("var2", "a")]),
        Point([("var1", 10), ("var2", "b")]),
        Point([("var1", 20), ("var2", "a")]),
        Point([("var1", 20), ("var2", "b")]),
    ]

    assert list(pm.keys()) == ["var1", "var2"]
    assert pm["var1"] == [10, 20]

    s = str(pm)
    assert "PointMeta" in s
    assert "var1" in s
    assert "name=" in s
    assert "cand_vals" in s

    assert pm.n_points == 4

    ps = [pm.point_i(i) for i in range(pm.n_points)]
    assert len(ps) == 4
    for target_p in target_ps:
        assert obj_in_objlist(target_p, ps)

    for bad_i in [-10, -1, 4, 10]:
        with pytest.raises(ValueError):
            _ = pm.point_i(bad_i)


@enforce_types
def test_point_meta_compare():
    pm1 = PointMeta([("var1", [10, 20]), ("var2", ["a", "b"])])

    pm2 = PointMeta([("var1", [10, 20]), ("var2", ["a", "b"])])
    assert pm1 == pm2

    pm3 = PointMeta([("var1", [10, 20]), ("ZZZ", ["a", "b"])])
    assert pm1 != pm3

    pm4 = PointMeta([("var1", [10, 20])])
    assert pm1 != pm4
