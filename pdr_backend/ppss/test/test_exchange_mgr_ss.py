import pytest
from enforce_typing import enforce_types

from pdr_backend.ppss.exchangemgr_ss import ExchangemgrSS


@enforce_types
def test_exchangemgr_ss_basic():
    d = (
        {
            "timeout": 30,
            "ccxt_params": {
                "createMarketBuyOrderRequiresPrice": False,
                "defaultType": "spot",
            },
            "dydx_params": {},
        },
    )
    ss = ExchangemgrSS(d)

    # yaml properties
    assert ss.timeout == 30
    assert ss.ccxt_params == _D["ccxt_params"]
    assert ss.dydx_params == _D["dydx_params"]

    # str
    assert "ExchangemgrSS" in str(ss)


@enforce_types
def test_exchangemgr_ss_test_dict__defaults():
    d = exchangemgr_ss_test_dict()
    ss = ExchangemgrSS(d)
    assert isinstance(ss.timeout, (int, float))
    assert 0 < ss.timeout < np.inf
    assert isinstance(ss.ccxt_params, dict)
    assert isinstance(ss.dydx_params, dict)


@enforce_types
def test_exchangemgr_ss_test_dict__specify_values():
    timeout = 123.456
    ccxt_params = {"foo": 2}
    dydx_params = {"bar": {"baz": "qux"}}
    d = exchangemgr_ss_test_dict(
        timeout=timeout,
        ccxt_params=ccxt_params,
        dydx_params=dydx_params,
    )
    ss = ExchangemgrSS(d)
    assert ss.timeout == timeout
    assert ss.ccxt_params == ccxt_params
    assert ss.dydx_params == dydx_params


@enforce_types
def test_exchangemgr_ss_timeout():
    # good: int
    ss = ExchangemgrSS(exchangemgr_ss_test_dict(timeout=77))
    assert ss.timeout == 77

    # good: float
    ss = ExchangemgrSS(exchangemgr_ss_test_dict(timeout=77.7))
    assert ss.timeout == 77.7

    # bad: string
    d = exchangemgr_ss_test_dict()
    d["timeout"] = "foo"
    with pytest.raises(TypeError):
        Exchangemgr(d)

    # bad: negative
    d = exchangemgr_ss_test_dict()
    d["timeout"] = -3
    with pytest.raises(ValueError):
        Exchangemgr(d)

    # bad: inf
    d = exchangemgr_ss_test_dict()
    d["timeout"] = np.inf
    with pytest.raises(ValueError):
        Exchangemgr(d)
