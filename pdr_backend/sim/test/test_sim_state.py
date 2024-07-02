from enforce_typing import enforce_types
import numpy as np
import pytest
from pytest import approx

from pdr_backend.sim.constants import Dirn, dirn_str, UP, DOWN
from pdr_backend.sim.sim_model_prediction import SimModelPrediction
from pdr_backend.sim.sim_state import (
    ClassifBaseData,
    TrueVsPredVals,
    HistPerfs,
    HistPerfs1Dir,
    Profits,
    SimState,
    PERFS_NAMES,
)

@enforce_types
def test_classif_base_data_1dir():
    d = TrueVsPredVals()
    assert d.truevals == []
    assert d.predprobs == []
    assert d.predvals == []
    assert d.n_correct == 0
    assert d.n_trials == 0

    # true = up, guess = up (correct guess)
    d.update(trueval=True, predprob=0.6)
    assert d.truevals == [True]
    assert d.predprobs == [0.6]
    assert d.predvals == [True]
    assert d.n_correct == 1
    assert d.n_trials == 1
    assert len(d.accuracy()) == 3
    assert d.accuracy()[0] == 1.0/1.0
    
    # true = down, guess = down (correct guess)
    d.update(trueval=False, predprob=0.3)
    assert d.truevals == [True, False]
    assert d.predprobs == [0.6, 0.3]
    assert d.predvals == [True, False]
    assert d.n_correct == 2
    assert d.n_trials == 2
    assert d.accuracy()[0] == 2.0/2.0
    
    # true = up, guess = down (incorrect guess)
    d.update(trueval=True, predprob=0.4)
    assert d.truevals == [True, False, True]
    assert d.predprobs == [0.6, 0.3, 0.4]
    assert d.predvals == [True, False, False]
    assert d.n_correct == 2
    assert d.n_trials == 3
    assert d.accuracy()[0] == approx(2.0/3.0)
    
    # true = down, guess = up (incorrect guess)
    d.update(trueval=False, predprob=0.7)
    assert d.truevals == [True, False, True, False]
    assert d.predprobs == [0.6, 0.3, 0.4, 0.7]
    assert d.predvals == [True, False, False, True]
    assert d.n_correct == 2
    assert d.n_trials == 4
    assert d.accuracy()[0] == approx(2.0/4.0)

    # test classifier metrics
    (acc_est, acc_l, acc_u) = d.accuracy()
    assert acc_est == approx(0.5)
    assert acc_l == approx(0.010009003864986377)
    assert acc_u == approx(0.9899909961350136)
    
    (precision, recall, f1) = d.precision_recall_f1()
    assert precision == approx(0.5)
    assert recall == approx(0.5)
    assert f1 == approx(0.5)
    
    loss = d.log_loss()
    assert loss == approx(0.7469410259762035)

@enforce_types
def test_classif_base_data():
    d = ClassifBaseData()
    assert isinstance(d[UP], TrueVsPredVals)
    assert isinstance(d[DOWN], TrueVsPredVals)

    # true was UP, both models were correct, 2x in a row
    p = SimModelPrediction(conf_thr=0.1, prob_UP=0.6, prob_DOWN=0.3)
    d.update(true_UP=True, true_DOWN=False, sim_model_p=p)
    d.update(true_UP=True, true_DOWN=False, sim_model_p=p)
    assert d[UP].truevals == [True, True]
    assert d[UP].predprobs == [0.6, 0.6]
    assert d[DOWN].truevals == [False, False]
    assert d[DOWN].predprobs == [0.3, 0.3]


@pytest.mark.parametrize("dirn", [UP, DOWN])
def test_hist_perfs_1dir(dirn):
    m = HistPerfs1Dir(dirn)

    assert m.acc_ests == m.acc_ls == m.acc_us == []
    assert m.f1s == m.precisions == m.recalls == []
    assert m.losses == []

    m.update(list(np.arange(0.1, 7.1, 1.0))) # 0.1, 1.1, ..., 6.1
    m.update(list(np.arange(0.2, 7.2, 1.0))) # 0.2, 1.2, ..., 6.2
    
    assert m.acc_ests == [0.1, 0.2]
    assert m.acc_ls == [1.1, 1.2]
    assert m.acc_us == [2.1, 2.2]
    assert m.f1s == [3.1, 3.2]
    assert m.precisions == [4.1, 4.2]
    assert m.recalls == [5.1, 5.2]
    assert m.losses == [6.1, 6.2]

    dirn_s = dirn_str(dirn)
    assert len(PERFS_NAMES) == 7
    target_metrics_names = [f"{name}_{dirn_s}" for name in PERFS_NAMES]
    assert m.recent_metrics_names() == target_metrics_names
    assert m.recent_metrics_names()[0] == "acc_est_UP"
    assert m.recent_metrics_names()[-1] == "loss_UP"

    metrics = m.recent_metrics_values()
    assert len(metrics) == 7
    assert metrics == {
        f"acc_est_{dirn_s}": 0.1,
        f"acc_l_{dirn_s}": 1.1,
        f"acc_u_{dirn_s}": 2.1,
        f"f1_{dirn_s}": 3.1,
        f"precision_{dirn_s}": 4.1,
        f"recall_{dirn_s}": 5.1,
        f"loss_{dirn_s}": 6.1,
    }

@enforce_types
def test_hist_perfs():
    hist_perfs = HistPerfs()
    assert isinstance(hist_perfs[UP], HistPerfs1Dir)
    assert isinstance(hist_perfs[DOWN], HistPerfs1Dir)

    classif_base_data = ClassifBaseData()
    p = SimModelPrediction(conf_thr=0.1, prob_UP=0.6, prob_DOWN=0.3)
    classif_base_data.update(true_UP=True, true_DOWN=False, sim_model_p=p)
    classif_base_data.update(true_UP=True, true_DOWN=False, sim_model_p=p)

    hist_perfs.update(classif_base_data)

    target_metrics_names = [f"{name}_{dirn_str(dirn)}"
                            for dirn in [UP, DOWN]
                            for name in PERFS_NAMES]
    assert len(target_metrics_names) == 7 * 2

    recent_names = hist_perfs.recent_metrics_names()
    assert recent_names == target_metrics_names
    assert recent_names[0] == "acc_est_UP"
    assert recent_names[1] == "acc_l_UP"
    assert recent_names[-1] == "loss_DOWN"

    metrics = hist_perfs.recent_metrics_values()
    assert len(metrics) == 7 * 2
    assert sorted(target_metrics_names) == sorted(metrics.keys())

    # given the metrics: accuracy, f1/precision/recall, and loss,
    # then nothing should be outside [0.0, 3.0]
    assert 0.0 <= min(metrics.values()) <= max(metrics.values()) <= 3.0

@enforce_types
def test_profits__attributes():
    p = Profits()
    assert p.pdr_profits_OCEAN == []
    assert p.trader_profits_USD == []
    
    p.update_pdr_profit(2.1)
    p.update_pdr_profit(2.2)
    assert p.pdr_profits_OCEAN == [2.1, 2.2]
    
    p.update_trader_profit(3.1)
    p.update_trader_profit(3.2)
    assert p.trader_profits_USD == [3.1, 3.2]

    assert Profits.recent_metrics_names() == \
        ["pdr_profit_OCEAN", "trader_profit_USD"]

@enforce_types
def test_profits__calc_pdr_profit():
    # true = up, guess = up (correct guess), others fully wrong
    profit = Profits.calc_pdr_profit(
        others_stake = 2000.0,
        others_accuracy = 0.0,
        stake_up = 1000.0,
        stake_down = 0.0,
        revenue = 2.0,
        true_up_close = True,
    )
    assert profit == 2002.0
    
    # true = down, guess = down (correct guess), others fully wrong
    profit = Profits.calc_pdr_profit(
        others_stake = 2000.0,
        others_accuracy = 0.0,
        stake_up = 0.0,
        stake_down = 1000.0,
        revenue = 2.0,
        true_up_close = False,
    )
    assert profit == 2002.0

    # true = up, guess = down (incorrect guess), others fully right
    profit = Profits.calc_pdr_profit(
        others_stake = 2000.0,
        others_accuracy = 100.0,
        stake_up = 0.0,
        stake_down = 1000.0,
        revenue = 2.0,
        true_up_close = True,
    )
    assert profit == -1000.0

    # true = down, guess = up (incorrect guess), others fully right
    profit = Profits.calc_pdr_profit(
        others_stake = 2000.0,
        others_accuracy = 100.0,
        stake_up = 1000.0,
        stake_down = 0.0,
        revenue = 2.0,
        true_up_close = False,
    )
    assert profit == -1000.0
    
    # true = up, guess = up AND down (half-correct), others fully wrong
    profit = Profits.calc_pdr_profit(
        others_stake = 1000.0,
        others_accuracy = 0.00,
        stake_up = 1000.0,
        stake_down = 100.0,
        revenue = 2.0,
        true_up_close = True,
    )
    assert profit == 502.0



@enforce_types
def test_sim_state():
    state = SimState()
    assert state.iter_number == 0
    assert state.sim_model_data is None
    assert state.sim_model is None
    assert isinstance(state.classif_base, ClassifBaseData)
    assert isinstance(state.hist_perfs, HistPerfs)
    assert isinstance(state.profits, Profits)

    state.iter_number = 1
    state.sim_model = "foo"
    state.init_loop_attributes()
    assert state.iter_number == 0
    assert state.sim_model is None

    names = state.recent_metrics_names()
    assert len(names) == 7 * 2 + 2

    # FIXME: need to add some data to state first
    metrics = state.recent_metrics_values()
    assert len(metrics) == 7 * 2 + 2
