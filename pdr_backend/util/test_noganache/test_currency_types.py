from enforce_typing import enforce_types
import pytest

from pdr_backend.util.currency_types import Eth, Wei


@enforce_types
def test_currency_types_base():
    assert Wei(int(1234 * 1e18)).to_eth() == Eth(1234)
    assert Wei(int(12.34 * 1e18)).to_eth() == Eth(12.34)
    assert Wei(int(0.1234 * 1e18)).to_eth() == Eth(0.1234)

    assert Eth(1234).to_wei() == Wei(1234 * 1e18) and type(Eth(1234).to_wei()) == Wei
    assert Eth(12.34).to_wei() == Wei(12.34 * 1e18)
    assert Eth(0.1234).to_wei() == Wei(0.1234 * 1e18)

    assert (
        Wei(int(12.34 * 1e18)).str_with_wei() == "12.34 eth (12340000000000000000 wei)"
    )


@enforce_types
def test_currency_types_math_on_Eth():
    # pylint: disable=pointless-statement
    x1, x2 = Eth(5.0), Eth(2.5)

    assert +x1 == Eth(5.0)
    assert -x1 == Eth(-5.0)

    assert (x1 + x2) == Eth(7.5)
    assert (x1 - x2) == Eth(2.5)
    assert (x2 - x1) == Eth(-2.5)

    assert (x1 * x2) == Eth(12.5)
    assert (x1 / x2) == Eth(2.0)
    assert (x2 / x1) == Eth(0.5)

    assert x1 * 2 == Eth(10.0)
    assert x1 * 2.0 == Eth(10.0)

    assert x1 / 2 == Eth(2.5)
    assert x1 / 2.5 == Eth(2.0)

    # don't bother overriding these (more complex)
    with pytest.raises(TypeError):
        2 * x1
    with pytest.raises(TypeError):
        2.0 * x1
    with pytest.raises(TypeError):
        10 / x1
    with pytest.raises(TypeError):
        10.0 / x1


@enforce_types
def test_currency_types_math_on_Wei():
    # pylint: disable=pointless-statement
    x1, x2 = Wei(5000), Wei(2500)

    assert +x1 == Wei(5000)
    assert -x1 == Wei(-5000)

    assert (x1 + x2) == Wei(7500)
    assert (x1 - x2) == Wei(2500)
    assert (x2 - x1) == Wei(-2500)
    assert x1 * x2 == Wei(5000 * 2500)
    assert x1 / x2 == Wei(5000 / 2500)

    # don't bother overriding these (more complex, or dangerous)

    with pytest.raises(TypeError):
        2 * x1
    with pytest.raises(TypeError):
        2.0 * x1
    with pytest.raises(TypeError):
        10 / x1
    with pytest.raises(TypeError):
        10.0 / x1


@enforce_types
def test_math_with_wei_and_eth():
    x1, x2 = Wei(5000), Eth(2.5)

    with pytest.raises(TypeError):
        x1 + x2

    with pytest.raises(TypeError):
        x1 - x2

    with pytest.raises(TypeError):
        x1 * x2

    with pytest.raises(TypeError):
        x1 / x2

    with pytest.raises(TypeError):
        x1 > x2

    with pytest.raises(TypeError):
        x1 < x2

    with pytest.raises(TypeError):
        x1 == x2
