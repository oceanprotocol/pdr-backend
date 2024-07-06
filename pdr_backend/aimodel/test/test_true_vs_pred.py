from enforce_typing import enforce_types
from pytest import approx

from pdr_backend.aimodel.true_vs_pred import PERF_NAMES, TrueVsPred


# pylint: disable=too-many-statements
@enforce_types
def test_true_vs_pred():
    d = TrueVsPred()
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
    assert d.accuracy()[0] == 1.0 / 1.0

    # true = down, guess = down (correct guess)
    d.update(trueval=False, predprob=0.3)
    assert d.truevals == [True, False]
    assert d.predprobs == [0.6, 0.3]
    assert d.predvals == [True, False]
    assert d.n_correct == 2
    assert d.n_trials == 2
    assert d.accuracy()[0] == 2.0 / 2.0

    # true = up, guess = down (incorrect guess)
    d.update(trueval=True, predprob=0.4)
    assert d.truevals == [True, False, True]
    assert d.predprobs == [0.6, 0.3, 0.4]
    assert d.predvals == [True, False, False]
    assert d.n_correct == 2
    assert d.n_trials == 3
    assert d.accuracy()[0] == approx(2.0 / 3.0)

    # true = down, guess = up (incorrect guess)
    d.update(trueval=False, predprob=0.7)
    assert d.truevals == [True, False, True, False]
    assert d.predprobs == [0.6, 0.3, 0.4, 0.7]
    assert d.predvals == [True, False, False, True]
    assert d.n_correct == 2
    assert d.n_trials == 4
    assert d.accuracy()[0] == approx(2.0 / 4.0)

    # test performance values
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

    assert d.perf_names() == PERF_NAMES
    assert len(d.perf_values()) == len(PERF_NAMES)

    target_values = [acc_est, acc_l, acc_u, precision, recall, f1, loss]
    values = d.perf_values()
    for val, target_val in zip(values, target_values):
        assert val == approx(target_val)
