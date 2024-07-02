from enforce_typing import enforce_types
import pytest
from pytest import approx

from pdr_backend.sim.sim_model_prediction import (
    SimModelPrediction,
    _do_trust_models,
    _models_in_conflict,
)

@enforce_types
def test_sim_model_prediction_case1_models_in_conflict():
    p = SimModelPrediction(conf_thr = 0.1, prob_UP = 0.6, prob_DOWN = 0.7)
    assert p.conf_thr == 0.1
    assert p.prob_UP == 0.6
    assert p.prob_DOWN == 0.7
    
    assert p.models_in_conflict()
    assert p.conf_up == 0.0
    assert p.conf_down == 0.0
    assert not p.pred_up
    assert not p.pred_down
    assert p.prob_up_MERGED == 0.5

@enforce_types
def test_sim_model_prediction_case2_up_dominates():
    p = SimModelPrediction(conf_thr = 0.1, prob_UP = 0.6, prob_DOWN = 0.3)
    assert p.conf_thr == 0.1
    assert p.prob_UP == 0.6
    assert p.prob_DOWN == 0.3
    
    assert not p.models_in_conflict()
    assert p.prob_UP >= p.prob_DOWN
    assert p.conf_up == approx((0.6 - 0.5) * 2.0) == approx(0.1 * 2.0) == 0.2
    assert p.conf_down == 0.0
    assert p.pred_up == (p.conf_up > p.conf_thr) == (0.2 > 0.1) == True
    assert not p.pred_down
    assert p.prob_up_MERGED == approx(0.6)

    # setup like above, but now with higher conf thr, which it can't exceed
    p = SimModelPrediction(conf_thr = 0.3, prob_UP = 0.6, prob_DOWN = 0.3)
    assert not p.pred_up
    
@enforce_types
def test_sim_model_prediction_case3_down_dominates():
    p = SimModelPrediction(conf_thr = 0.1, prob_UP = 0.4, prob_DOWN = 0.7)
    assert p.conf_thr == 0.1
    assert p.prob_UP == 0.4
    assert p.prob_DOWN == 0.7
    
    assert not p.models_in_conflict()
    assert not (p.prob_UP >= p.prob_DOWN)
    assert p.prob_DOWN > p.prob_UP
    assert p.conf_up == 0.0
    assert p.conf_down == approx((0.7 - 0.5) * 2.0) == approx(0.2 * 2.0) == 0.4
    assert not p.pred_up
    assert p.pred_down == (p.conf_down > p.conf_thr) == (0.4 > 0.1) == True
    assert p.prob_up_MERGED == approx(1.0 - 0.7) == approx(0.3)
    
    # setup like above, but now with higher conf thr, which it can't exceed
    p = SimModelPrediction(conf_thr = 0.5, prob_UP = 0.4, prob_DOWN = 0.7)
    assert not p.pred_down


@enforce_types
def test_do_trust_models_unhappy_path():
    for tup in [
            # out of range
            (True, False, -1.4, 0.6),
            (True, False, 1.4, 0.6),
            (True, False, 0.4, -1.6),
            (True, False, 0.4, 1.6),
            # values conflict
            (True, True, 0.4, 0.6), # pred_up and pred_down
            (True, False, 0.4, 0.6), # pred_up and prob_DOWN > prob_UP
            (False, True, 0.6, 0.4), # pred_down and prob_UP > prob_DOWN
    ]:
        (pred_up, pred_down, prob_UP, prob_DOWN) = tup
        with pytest.raises(ValueError):
            _do_trust_models(pred_up, pred_down, prob_UP, prob_DOWN)
            print(f"Should have failed on {tup}")
        
@enforce_types
def test_do_trust_models_happy_path():
    assert _do_trust_models(True, False, 0.6, 0.4)
    assert _do_trust_models(False, True, 0.4, 0.6)
    
    assert not _do_trust_models(False, False, 0.4, 0.6)
    assert not _do_trust_models(False, True, 0.4, 0.4)
    assert not _do_trust_models(False, True, 0.6, 0.6)
    
@enforce_types
def test_models_in_conflict_unhappy_path():
    for (prob_UP, prob_DOWN) in [
        (-1.6, 0.6),
        (1.6, 0.6),
        (0.6, -1.6),
        (0.6, 1.6),
    ]:
        with pytest.raises(ValueError):
            _models_in_conflict(prob_UP, prob_DOWN)

@enforce_types
def test_models_in_conflict_happy_path():
    assert _models_in_conflict(0.6, 0.6)
    assert _models_in_conflict(0.4, 0.4)
    
    assert not _models_in_conflict(0.6, 0.4)
    assert not _models_in_conflict(0.4, 0.6)
    assert not _models_in_conflict(0.5, 0.5)

    
