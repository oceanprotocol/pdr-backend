from enforce_typing import enforce_types

from pdr_backend.sim.sim_state import (
    ClassifBaseData,
    ClassifBaseData1Dir,
)

@enforce_types
def test_classif_base_data_1dir():
    d = ClassifBaseData1Dir()
    assert d.ytrues == []
    assert d.probs_up == []
    assert d.ytrues_hat == []
    assert d.n_correct == 0
    assert d.n_trials == 0

    # true = up, guess = up (correct guess)
    d.update(true_up=True, prob_up=0.6)
    assert d.ytrues == [True]
    assert d.probs_up == [0.6]
    assert d.ytrues_hat == [True]
    assert d.n_correct == 1
    assert d.n_trials == 1
    assert len(d.accuracy()) == 3
    assert d.accuracy()[0] == 1.0/1.0
    
    # true = down, guess = down (correct guess)
    d.update(true_up=False, prob_up=0.3)
    assert d.ytrues == [True, False]
    assert d.probs_up == [0.6, 0.3]
    assert d.ytrues_hat == [True, False]
    assert d.n_correct == 2
    assert d.n_trials == 2
    assert d.accuracy()[0] == 2.0/2.0
    
    # true = up, guess = down (incorrect guess)
    d.update(true_up=True, prob_up=0.4)
    assert d.ytrues == [True, False, True]
    assert d.probs_up == [0.6, 0.3, 0.4]
    assert d.ytrues_hat == [True, False, False]
    assert d.n_correct == 2
    assert d.n_trials == 3
    assert d.accuracy()[0] == approx(2.0/3.0)
    
    # true = down, guess = up (incorrect guess)
    d.update(true_up=False, prob_up=0.7)
    assert d.ytrues == [True, False, True, False]
    assert d.probs_up == [0.6, 0.3, 0.4, 0.7]
    assert d.ytrues_hat == [True, False, False, True]
    assert d.n_correct == 2
    assert d.n_trials == 4
    assert d.accuracy()[0] == approx(2.0/4.0)

@enforce_types
def test_classif_base_data():
    d_UP = ClassifBaseData1Dir()
    d_DOWN = ClassifBaseData1Dir()
    d = ClassifBaseData(d_UP, d_DOWN)
    assert id(d[UP]) == id(d_UP)
    assert id(d[DOWN]) == id(d_DOWN)
    
    p = SimModelPrediction(FIXME)
    d.update(true_up_UP, prob_up_UP, p)

    raise NotImplementedError("Build the rest of me")


@enforce_types
def test_classif_metrics_1dir():
    raise NotImplementedError("Build me")


@enforce_types
def test_classif_metrics():
    raise NotImplementedError("Build me")


@enforce_types
def test_profits():
    raise NotImplementedError("Build me")
    


@enforce_types
def test_sim_state():
    raise NotImplementedError("Build me")
