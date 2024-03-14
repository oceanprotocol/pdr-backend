from enforce_typing import enforce_types
import pytest

from pdr_backend.ppss.multisim_ss import MultisimSS, multisim_ss_test_dict
from pdr_backend.ppss.ppss import fast_test_yaml_str, PPSS


@enforce_types
def test_multisim_ss_from_yaml_str(tmpdir):
    yaml_str = fast_test_yaml_str(tmpdir)
    ppss = PPSS(yaml_str=yaml_str, network="development")
    ss = ppss.multisim_ss
    assert isinstance(ss, MultisimSS)

    assert ss.approach == "SimpleSweep"
    assert isinstance(ss.sweep_params, list)
    assert ss.sweep_params
    assert ss.n_points() > 1

    assert "MultisimSS" in str(ss)


@enforce_types
def test_multisim_ss_from_dict(tmpdir):
    sweep_params = [
        {"predictoor_ss.aimodel_ss.max_n_train": "500, 1000, 1500"},
        {"predictoor_ss.aimodel_ss.autoregressive_n": "1, 2"},
        {"predictoor_ss.aimodel_ss.balance_classes": "None, SMOTE"},
        {"trader_ss.buy_amt": "1000 USD, 2000 USD"},
    ]
    d = {
        "approach": "SimpleSweep",
        "sweep_params": sweep_params,
    }
    ss = MultisimSS(d)
    assert isinstance(ss, MultisimSS)

    assert ss.approach == "SimpleSweep"
    assert ss.sweep_params == sweep_params
    assert ss.n_points() == 3 * 2 * 2 * 2

    assert "MultisimSS" in str(ss)


@enforce_types
def test_multisim_ss_unhappy_inputs():
    d = multisim_ss_test_dict(approach="foo")
    with pytest.raises(ValueError):
        MultisimSS(d)


@enforce_types
def test_multisim_ss_test_dict():
    d = multisim_ss_test_dict()
    assert d["approach"] == "SimpleSweep"
    assert d["sweep_params"]

    ss = MultisimSS(d)
    assert ss.approach == "SimpleSweep"
    assert ss.sweep_params
    assert ss.n_points() > 1


@enforce_types
def test_multisim_ss_points1(tmpdir):
    sweep_params = [
        {"predictoor_ss.approach": "1, 2"},
        {"trader_ss.buy_amt": "10 USD, 20 USD"},
    ]
    ss = MultisimSS(multisim_ss_test_dict(sweep_params=sweep_params))

    target_points = [
        {'trader_ss.buy_amt' : '10 USD', 'predictoor_ss.approach' : "1"},
        {'trader_ss.buy_amt' : '10 USD', 'predictoor_ss.approach' : "2"},
        {'trader_ss.buy_amt' : '20 USD', 'predictoor_ss.approach' : "1"},
        {'trader_ss.buy_amt' : '20 USD', 'predictoor_ss.approach' : "2"},
        ]
    
    assert ss.n_points() == 4

    points = [ss.point_i(i) for i in range(ss.n_points)]
    assert len(points) == 4
    import pdb; pdb.set_trace()
    assert set(points) == set(target_points)
    assert sorted(points) == sorted(target_points)
        
