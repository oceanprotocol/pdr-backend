from enforce_typing import enforce_types

from pdr_backend.simulation import timeblock


@enforce_types
def test_timeblock():
    z = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]

    X = timeblock.timeblock(z, 4)

    assert list(X[0, :]) == [5, 4, 3, 2]
    assert list(X[1, :]) == [6, 5, 4, 3]
    assert list(X[2, :]) == [7, 6, 5, 4]
    assert list(X[3, :]) == [8, 7, 6, 5]
    assert list(X[4, :]) == [9, 8, 7, 6]
    assert list(X[5, :]) == [10, 9, 8, 7]

    assert X.shape[0] == 6
    assert X.shape[1] == 4
