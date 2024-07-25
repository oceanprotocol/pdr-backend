from enforce_typing import enforce_types
import pytest

from pdr_backend.aimodel.aimodel_data_factory import _slice


@enforce_types
def test_slice__happy_path():
    x = [1, 2, 3, 4, 5, 6, 7]
    assert _slice(x=x, st=-2, fin=0) == [6, 7]
    assert _slice(x=x, st=-3, fin=-1) == [5, 6]
    assert _slice(x=x, st=-7, fin=-5) == [1, 2]
    assert _slice(x=x, st=-7, fin=-6) == [1]
    assert _slice(x=x, st=-7, fin=0) == x
    assert _slice(x=[1], st=-1, fin=0) == [1]


@enforce_types
def test_slice__unhappy_path():
    # need st < 0
    with pytest.raises(AssertionError):
        _ = _slice(x=[1, 2, 3], st=0, fin=-2)

    # need fin <= 0
    with pytest.raises(AssertionError):
        _ = _slice(x=[1, 2, 3], st=-2, fin=1)

    # need st < fin
    with pytest.raises(AssertionError):
        _ = _slice(x=[1, 2, 3], st=-4, fin=-4)

    with pytest.raises(AssertionError):
        _ = _slice(x=[1, 2, 3], st=-4, fin=-5)

    # st out of bounds
    with pytest.raises(AssertionError):
        _slice(x=[1, 2, 3, 4, 5, 6, 7], st=-8, fin=-5)

    with pytest.raises(AssertionError):
        _slice(x=[], st=-1, fin=0)
