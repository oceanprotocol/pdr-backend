from enforce_typing import enforce_types
import numpy as np
import pytest

from pdr_backend.ppss.exchange_mgr_ss import (
    ExchangeMgrSS,
    exchange_mgr_ss_test_dict,
)


@enforce_types
def test_exchange_mgr_ss_basic():
    d = {
        "timeout": 30,
        "ccxt_params": {
            "createMarketBuyOrderRequiresPrice": False,
            "defaultType": "spot",
        },
        "dydx_params": {},
    }
    ss = ExchangeMgrSS(d)

    # yaml properties
    assert ss.timeout == 30
    assert ss.ccxt_params == d["ccxt_params"]
    assert ss.dydx_params == d["dydx_params"]

    # str
    assert "ExchangeMgrSS" in str(ss)


@enforce_types
def test_exchange_mgr_ss_test_dict__defaults():
    d = exchange_mgr_ss_test_dict()
    ss = ExchangeMgrSS(d)
    assert isinstance(ss.timeout, (int, float))
    assert 0 < ss.timeout < np.inf
    assert isinstance(ss.ccxt_params, dict)
    assert isinstance(ss.dydx_params, dict)


@enforce_types
def test_exchange_mgr_ss_test_dict__specify_values():
    timeout = 123.456
    ccxt_params = {"foo": 2}
    dydx_params = {"bar": {"baz": "qux"}}
    d = exchange_mgr_ss_test_dict(
        timeout=timeout,
        ccxt_params=ccxt_params,
        dydx_params=dydx_params,
    )
    ss = ExchangeMgrSS(d)
    assert ss.timeout == timeout
    assert ss.ccxt_params == ccxt_params
    assert ss.dydx_params == dydx_params


@enforce_types
def test_exchange_mgr_ss_timeout():
    # good: int
    ss = ExchangeMgrSS(exchange_mgr_ss_test_dict(timeout=77))
    assert ss.timeout == 77

    # good: float
    ss = ExchangeMgrSS(exchange_mgr_ss_test_dict(timeout=77.7))
    assert ss.timeout == 77.7

    # bad: string
    d = exchange_mgr_ss_test_dict()
    d["timeout"] = "foo"
    with pytest.raises(TypeError):
        ExchangeMgrSS(d)

    # bad: negative
    d = exchange_mgr_ss_test_dict()
    d["timeout"] = -3
    with pytest.raises(ValueError):
        ExchangeMgrSS(d)

    # bad: inf
    d = exchange_mgr_ss_test_dict()
    d["timeout"] = np.inf
    with pytest.raises(ValueError):
        ExchangeMgrSS(d)


@enforce_types
def test_exchange_mgr_ss_ccxt_params():
    _test_exchange_mtr_dict_params("ccxt_params")

    
@enforce_types
def test_exchange_mgr_ss_dydx_params():
    _test_exchange_mtr_dict_params("dydx_params")

    
@enforce_types
def _test_exchange_mtr_dict_params(params_name: str):
    # good: dict of str:any
    d = exchange_mgr_ss_test_dict()
    d[params_name] = {"foo":7, "bar":"baz", "bah":None}        
    ss = ExchangeMgrSS(d)
    assert getattr(ss, params_name) == {"foo": 7, "bar":"baz", "bah":None}
        
    # bad: non-dict
    for non_dict in ["foo", 3, None]:
        d = exchange_mgr_ss_test_dict()
        d[params_name] = non_dict
        with pytest.raises(TypeError):
            ss = ExchangeMgrSS(d)

    # bad: dict of non-str:any
    for non_str in [7, 7.7, None]:
        d = exchange_mgr_ss_test_dict()
        d[params_name] = {non_str: "foo"}
        with pytest.raises(TypeError):
            ss = ExchangeMgrSS(d)
