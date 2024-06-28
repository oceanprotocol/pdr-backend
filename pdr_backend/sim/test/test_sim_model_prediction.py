rom enforce_typing import enforce_types

from pdr_backend.sim.sim_model_prediction import (
    SimModelPrediction,
    _do_trust_models,
    _models_in_conflict,
)

@enforce_types
def test_sim_model_prediction_case1_models_in_conflict():
    p = SimModelPrediction(conf_thr = 0.1, prob_up_UP = 0.6, prob_up_DOWN = 0.3)
    assert p.conf_thr == 0.1
    assert p.prob_up_UP == 0.6
    assert p.prob_up_DOWN = 0.3

    assert p.prob_down_DOWN = 1.0 - 0.3 == 0.7
    
    assert p.models_in_conflict()
    assert p.conf_up == 0.0
    assert p.conf_down == 0.0
    assert not p.pred_up
    assert not p.pred_down
    assert p.prob_up_MERGED == 0.5

@enforce_types
def test_sim_model_prediction_case2_up_dominates():
    p = SimModelPrediction(conf_thr = 0.1, prob_up_UP = 0.6, prob_up_DOWN = 0.7)
    assert p.conf_thr == 0.1
    assert p.prob_up_UP == 0.6
    assert p.prob_up_DOWN = 0.7

    assert p.prob_down_DOWN = 1.0 - 0.7 == 0.3
    
    assert not p.models_in_conflict()
    assert p.prob_up_UP >= p.prob_down_DOWN
    assert p.conf_up == (0.6 - 0.5) * 2.0 == 0.1 * 2.0 == 0.2
    assert p.conf_down == 0.0
    assert p.pred_up == p.conf_up > p.conf_thr == 0.2 > 0.1 == True
    assert not p.pred_down
    assert p.prob_up_MERGED == 0.6

    # setup like above, but now with higher confidence level, which it can't exceed
    p = SimModelPrediction(conf_thr = 0.3, prob_up_UP = 0.6, prob_up_DOWN = 0.7)
    assert not p.pred_up
    
@enforce_types
def test_sim_model_prediction_case3_down_dominates():
    p = SimModelPrediction(conf_thr = 0.1, prob_up_UP = 0.4, prob_up_DOWN = 0.3)
    assert p.conf_thr == 0.1
    assert p.prob_up_UP == 0.4
    assert p.prob_up_DOWN = 0.3

    assert p.prob_down_DOWN = 1.0 - 0.3 == 0.7
    
    assert not p.models_in_conflict()
    assert not (p.prob_up_UP >= p.prob_down_DOWN)
    assert prob_down_DOWN > prob_up_UP
    assert p.conf_up == 0.0
    assert p.conf_down == (0.7 - 0.5) * 2.0 == 0.2 * 2.0 == 0.4
    assert not p.pred_up
    assert p.pred_down == (p.conf_down > p.conf_thr) == 0.4 > 0.1 == True
    assert p.prob_up_MERGED == 1.0 - 0.7 == 0.3
    
    # setup like above, but now with higher confidence level, which it can't exceed
    p = SimModelPrediction(conf_thr = 0.5, prob_up_UP = 0.4, prob_up_DOWN = 0.3)
    assert not p.pred_down


@enforce_types
def test_do_trust_models():    
    with pytest.raises(ValueError):
        _ = _do_trust_models(True, True, 0.4, 0.6)
        
    with pytest.raises(ValueError):
        _ = _do_trust_models(True, False, 0.4, 0.6)
        
    with pytest.raises(ValueError):
        _ = _do_trust_models(False, True, 0.6, 0.6)
        
    with pytest.raises(ValueError):
        _do_trust_models(True, False, -1.4, 0.6)
    with pytest.raises(ValueError):
        _do_trust_models(True, False, 1.4, 0.6)
        
    with pytest.raises(ValueError):
        _do_trust_models(True, False, 0.4, -1.6)
    with pytest.raises(ValueError):
        _do_trust_models(True, False, 0.4, 1.6)
        
    assert _do_trust_models(True, False, 0.4, 0.6)
    assert _do_trust_models(False, True, 0.4, 0.6)
    
    assert not _do_trust_models(False, False, 0.4, 0.6)
    assert not _do_trust_models(False, True, 0.4, 0.4)
    assert not _do_trust_models(False, True, 0.6, 0.6)


    
@enforce_types
def test_models_in_conflict():    
    with pytest.raises(ValueError):
        _models_in_conflict(-1.6, 0.6)
    with pytest.raises(ValueError):
        _models_in_conflict(1.6, 0.6)
        
    with pytest.raises(ValueError):
        _models_in_conflict(0.6, -1.6)
    with pytest.raises(ValueError):
        _models_in_conflict(0.6, 1.6)
        
    assert _models_in_conflict(0.6, 0.6)
    assert _models_in_conflict(0.4, 0.4)
    
    assert not _models_in_conflict(0.6, 0.4)
    assert not _models_in_conflict(0.4, 0.6)
    assert not _models_in_conflict(0.5, 0.5)

    
