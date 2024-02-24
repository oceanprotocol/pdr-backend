import warnings

import numpy as np
from numpy.testing import assert_array_equal
import pytest
from enforce_typing import enforce_types

from pdr_backend.aimodel.plot_model import plot_model
from pdr_backend.aimodel.aimodel_data_factory import AimodelDataFactory
from pdr_backend.aimodel.aimodel_factory import AimodelFactory
from pdr_backend.ppss.aimodel_ss import APPROACHES, AimodelSS
from pdr_backend.util.mathutil import classif_acc

PLOT = True # only turn on for manual testing

@enforce_types
def test_aimodel_factory_LinearLogistic():
    _test_aimodel_factory(approach="LinearLogistic")
    
@enforce_types
def test_aimodel_factory_LinearSVC():
    _test_aimodel_factory(approach="LinearSVC")

@enforce_types
def _test_aimodel_factory(approach):
    # settings
    aimodel_ss = AimodelSS(
        {
            "approach": approach,
            "max_n_train": 7,
            "autoregressive_n": 3,
            "input_feeds": ["binance BTC/USDT c"],
        }
    )

    # factory
    factory = AimodelFactory(aimodel_ss)

    # data
    y_thr = 2.0
    
    N = 1000
    mn, mx = -10.0, +10.0
    X = np.random.uniform(mn, mx, (N, 2))
    ycont = 3.0 + 1.0 * X[:, 0] + 2.0 * X[:, 1] # ycont = 3 + 1*x0 + 2*x1
    ytrue = ycont > y_thr

    # build model
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # ignore ConvergenceWarning, more
        model = factory.build(X, ytrue)

    # plot
    if PLOT:
        labels = ("x0", "x1")
        fancy_title = True
        leg_loc = "upper right"
        fig_ax = None
        xranges = (mn, mx, mn, mx)
        plot_model(
            model, X, ytrue, labels,
            fig_ax = None,
            xranges = (mn, mx, mn, mx),
            fancy_title = True,
            legend_loc = "upper right",
        )

    # test predict_true() & predict_ptrue()
    ytrue_hat = model.predict_true(X)
    yptrue_hat = model.predict_ptrue(X)

    assert ytrue_hat.shape == yptrue_hat.shape == (N,)
    assert ytrue_hat.dtype == bool
    assert yptrue_hat.dtype == float
    
    assert classif_acc(ytrue_hat, ytrue) > 0.8
    assert 0 < min(yptrue_hat) < max(yptrue_hat) < 1.0
    assert_array_equal(yptrue_hat > 0.5, ytrue_hat)

    assert not PLOT



@enforce_types
def test_aimodel_accuracy_from_create_xy(aimodel_factory):
    # This is from a test function in test_model_data_factory.py

    # The underlying AR process is: close[t] = close[t-1] + open[t-1]
    X_trn = np.array(
        [
            [0.1, 0.1, 3.1, 4.2],  # oldest
            [0.1, 0.1, 4.2, 5.3],
            [0.1, 0.1, 5.3, 6.4],
            [0.1, 0.1, 6.4, 7.5],
            [0.1, 0.1, 7.5, 8.6],
        ]
    )  # newest
    ycont_trn = np.array([5.3, 6.4, 7.5, 8.6, 9.7])  # oldest  # newest
    
    y_thr = 7.0
    ytrue_trn = AimodelDataFactory.ycont_to_ytrue(ycont_trn, y_thr)

    model = aimodel_factory.build(X_trn, ytrue_trn)

    ytrue_trn_hat = model.predict_true(X_trn)
    assert_array_equal(ytrue_trn, ytrue_trn_hat) # expect zero error

    yptrue_trn_hat = model.predict_ptrue(X_trn)
    assert_array_equal(yptrue_trn_hat > 0.5, ytrue_trn_hat)

