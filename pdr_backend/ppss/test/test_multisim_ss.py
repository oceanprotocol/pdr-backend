from enforce_typing import enforce_types
import pytest

from pdr_backend.ppss.multisim_ss import MultisimSS, multisim_ss_test_dict
from pdr_backend.ppss.ppss import fast_test_yaml_str, PPSS
from pdr_backend.util.listutil import obj_in_objlist
from pdr_backend.util.point import Point
from pdr_backend.util.point_meta import PointMeta


@enforce_types
def test_multisim_ss_from_yaml_str(tmpdir):
    yaml_str = fast_test_yaml_str(tmpdir)
    ppss = PPSS(yaml_str=yaml_str, network="development")
    ss = ppss.multisim_ss
    assert isinstance(ss, MultisimSS)

    assert ss.approach == "SimpleSweep"
    assert isinstance(ss.sweep_params, list)
    assert ss.sweep_params
    assert ss.n_points > 1
    assert ss.n_runs == ss.n_points  # alias

    assert "MultisimSS" in str(ss)


@enforce_types
def test_multisim_ss_from_dict():
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
    assert ss.approach == "SimpleSweep"
    assert ss.sweep_params == sweep_params
    assert ss.n_points == 3 * 2 * 2 * 2
    assert ss.n_runs == ss.n_points  # alias


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
    assert ss.n_points > 1


@enforce_types
def test_multisim_ss_points1_basic():
    var1 = "predictoor_ss.approach"
    var2 = "trader_ss.buy_amt"
    sweep_params = [
        {var1: "1, 2"},
        {var2: "10 USD, 20 USD"},
    ]
    ss = MultisimSS(multisim_ss_test_dict(sweep_params=sweep_params))

    target_point_meta = PointMeta(
        [
            (var1, ["1", "2"]),
            (var2, ["10 USD", "20 USD"]),
        ]
    )

    target_points = [
        Point([(var1, "1"), (var2, "10 USD")]),
        Point([(var1, "1"), (var2, "20 USD")]),
        Point([(var1, "2"), (var2, "10 USD")]),
        Point([(var1, "2"), (var2, "20 USD")]),
    ]

    assert ss.n_points == 2 * 2
    assert ss.point_meta == target_point_meta

    points = [ss.point_i(i) for i in range(ss.n_points)]
    assert len(points) == 4
    for target_p in target_points:
        assert obj_in_objlist(target_p, points)


@enforce_types
def test_multisim_ss_points2_sweepfeeds():
    """
    Example in ppss.yaml:

    multisim_ss:
      approach: ...
      sweep_params:
      - predictoor_ss.aimodel_ss.max_n_train: 500, 1000
      - predictoor_ss.aimodel_ss.input_feeds:
        -
          - binance BTC/USDT c 5m
        -
          - binance BTC/USDT ETH/USDT c 5m
        -
          - binance BTC/USDT c 5m
          - kraken BTC/USDT c 5m
    """
    var1 = "predictoor_ss.aimodel_ss.max_n_train"
    var2 = "predictoor_ss.aimodel_ss.input_feeds"
    feeds1 = ["binance BTC/USDT c 5m"]
    feeds2 = ["binance BTC/USDT ETH/USDT c 5m"]
    feeds3 = ["binance BTC/USDT c 5m", "kraken BTC/USDT c 5m"]
    sweep_params = [
        {var1: "500, 1000"},
        {var2: [feeds1, feeds2, feeds3]},
    ]
    ss = MultisimSS(multisim_ss_test_dict(sweep_params=sweep_params))

    target_point_meta = PointMeta(
        [
            (var1, ["500", "1000"]),
            (var2, [feeds1, feeds2, feeds3]),
        ]
    )

    target_points = [
        Point([(var1, "500"), (var2, feeds1)]),
        Point([(var1, "500"), (var2, feeds2)]),
        Point([(var1, "500"), (var2, feeds3)]),
        Point([(var1, "1000"), (var2, feeds1)]),
        Point([(var1, "1000"), (var2, feeds2)]),
        Point([(var1, "1000"), (var2, feeds3)]),
    ]

    assert ss.n_points == 2 * 3
    assert ss.point_meta == target_point_meta

    points = [ss.point_i(i) for i in range(ss.n_points)]
    assert len(points) == 6
    for target_p in target_points:
        assert obj_in_objlist(target_p, points)
