from enforce_typing import enforce_types
import pytest

from pdr_backend.binmodel.constants import Dirn, dirn_str, UP, DOWN


@enforce_types
def test_binmodel_constants__basic():
    assert UP == Dirn.UP
    assert DOWN == Dirn.DOWN

    assert UP in Dirn
    assert DOWN in Dirn

    assert 1 in Dirn
    assert 2 in Dirn
    assert 0 not in Dirn
    assert 3 not in Dirn
    assert "up" not in Dirn


@enforce_types
def test_binmodel_constants__dirn_str():
    assert dirn_str(UP) == "UP"
    assert dirn_str(DOWN) == "DOWN"
    with pytest.raises(TypeError):
        _ = dirn_str(3)
    with pytest.raises(TypeError):
        _ = dirn_str("not an int")


@enforce_types
def test_binmodel_constants__can_sort():
    # this is possible because Dirn inherits from IntEnum, vs Enum :)
    assert sorted([Dirn.UP, Dirn.DOWN]) == [Dirn.UP, Dirn.DOWN]
    assert sorted([UP, DOWN]) == [UP, DOWN]
