from unittest.mock import Mock

import numpy as np
from enforce_typing import enforce_types
from numpy.testing import assert_array_equal
from plotly.graph_objs._figure import Figure
from pytest import approx

from pdr_backend.aimodel.aimodel_data_factory import AimodelDataFactory
from pdr_backend.aimodel.aimodel_factory import AimodelFactory
from pdr_backend.aimodel.aimodel_plotdata import AimodelPlotdata
from pdr_backend.aimodel.aimodel_plotter import (
    plot_aimodel_response,
    plot_aimodel_varimps,
)
from pdr_backend.ppss.aimodel_ss import AimodelSS, aimodel_ss_test_dict
from pdr_backend.util.mathutil import classif_acc

SHOW_PLOT = False  # only turn on for manual testing


@enforce_types
def test_aimodel_factory_2vars_LinearLogistic():
    _test_aimodel_factory_2vars_main(approach="LinearLogistic")


@enforce_types
def test_aimodel_factory_2vars_LinearSVC():
    _test_aimodel_factory_2vars_main(approach="LinearSVC")


@enforce_types
def test_aimodel_factory_2vars_Constant():
    _test_aimodel_factory_2vars_main(approach="Constant")


@enforce_types
def _test_aimodel_factory_2vars_main(approach):
    # settings, factory
    ss = AimodelSS(aimodel_ss_test_dict(approach=approach))
    factory = AimodelFactory(ss)

    # data
    y_thr = 2.0

    N = 1000
    mn, mx = -10.0, +10.0
    X = np.random.uniform(mn, mx, (N, 2))
    ycont = 3.0 + 1.0 * X[:, 0] + 2.0 * X[:, 1]  # ycont = 3 + 1*x0 + 2*x1
    ytrue = ycont > y_thr

    # build model
    model = factory.build(X, ytrue, show_warnings=False)

    # test predict_true() & predict_ptrue()
    ytrue_hat = model.predict_true(X)
    yptrue_hat = model.predict_ptrue(X)

    assert ytrue_hat.shape == yptrue_hat.shape == (N,)
    assert ytrue_hat.dtype == bool
    assert yptrue_hat.dtype == float

    if approach != "Constant":
        assert classif_acc(ytrue_hat, ytrue) > 0.8
        assert 0 < min(yptrue_hat) < max(yptrue_hat) < 1.0
    assert_array_equal(yptrue_hat > 0.5, ytrue_hat)

    # test variable importances
    imps = model.importance_per_var()
    assert sum(imps) == approx(1.0, 0.01)
    assert imps[0] == approx(0.333, abs=0.3)
    assert imps[1] == approx(0.667, abs=0.3)

    # plot
    colnames = ["x0", "x1"]
    slicing_x = np.array([0.0, 1.0])  # arbitrary
    d = AimodelPlotdata(model, X, ytrue, colnames, slicing_x)
    figure = plot_aimodel_response(d)
    assert isinstance(figure, Figure)


@enforce_types
def test_aimodel_factory_constantdata():
    # approach cannot be constant! That has to emerge
    ss = AimodelSS(aimodel_ss_test_dict(weight_recent="None"))
    factory = AimodelFactory(ss)

    N = 1000
    X = np.random.uniform(-10.0, +10.0, (N, 2))

    ytrue = np.full((N,), True)
    model = factory.build(X, ytrue)
    assert_array_equal(model.predict_true(X), np.full((N,), True))
    assert_array_equal(model.predict_ptrue(X), np.full((N,), 1.0))

    ytrue = np.full((N,), False)
    model = factory.build(X, ytrue)
    assert_array_equal(model.predict_true(X), np.full((N,), False))
    assert_array_equal(model.predict_ptrue(X), np.full((N,), 0.0))


@enforce_types
def test_aimodel_accuracy_from_create_xy():
    ss = AimodelSS(aimodel_ss_test_dict(weight_recent="None"))
    aimodel_factory = AimodelFactory(ss)

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
    assert_array_equal(ytrue_trn, ytrue_trn_hat)  # expect zero error

    yptrue_trn_hat = model.predict_ptrue(X_trn)
    assert_array_equal(yptrue_trn_hat > 0.5, ytrue_trn_hat)


@enforce_types
def test_aimodel_factory_1var_main():
    """1 input var. It will plot that var on both axes"""
    # settings, factory
    ss = AimodelSS(aimodel_ss_test_dict(approach="LinearLogistic"))
    factory = AimodelFactory(ss)

    # data
    N = 50
    mn, mx = -10.0, +10.0
    X = np.random.uniform(mn, mx, (N, 1))
    ycont = 3.0 + 4.0 * X[:, 0]
    y_thr = np.average(ycont)  # avg gives good class balance
    ytrue = ycont > y_thr

    # build model
    model = factory.build(X, ytrue, show_warnings=False)

    # test variable importances
    imps = model.importance_per_var()
    assert_array_equal(imps, np.array([1.0]))

    # plot
    colnames = ["x0"]
    slicing_x = np.array([0.1])  # arbitrary
    aimodel_plotdata = AimodelPlotdata(model, X, ytrue, colnames, slicing_x)
    figure = plot_aimodel_response(aimodel_plotdata)
    assert isinstance(figure, Figure)


@enforce_types
def test_aimodel_factory_4vars_response():
    """4 input vars. It will plot the 2 most important vars"""
    # settings, factory
    ss = AimodelSS(aimodel_ss_test_dict(approach="LinearLogistic"))
    factory = AimodelFactory(ss)

    # data
    N = 1000
    mn, mx = -10.0, +10.0
    X = np.random.uniform(mn, mx, (N, 4))
    ycont = 3.0 + 4.0 * X[:, 0] + 3.0 * X[:, 1] + 2.0 * X[:, 2] + 1.0 * X[:, 3]
    y_thr = np.average(ycont)  # avg gives good class balance
    ytrue = ycont > y_thr
    colnames = ["x0", "x1", "x3", "x4"]

    # build model
    model = factory.build(X, ytrue, show_warnings=False)

    # test variable importances
    imps = model.importance_per_var()
    assert imps[0] > imps[1] > imps[2] > imps[3] > 0.0
    assert sum(imps) == approx(1.0, 0.01)
    assert imps[0] == approx(4.0 / 10.0, abs=0.2)
    assert imps[1] == approx(3.0 / 10.0, abs=0.2)
    assert imps[2] == approx(2.0 / 10.0, abs=0.2)
    assert imps[3] == approx(1.0 / 10.0, abs=0.2)

    # plot model response
    slicing_x = np.array([0.1, 1.0, 2.0, 3.0])  # arbitrary
    aimodel_plotdata = AimodelPlotdata(model, X, ytrue, colnames, slicing_x)

    figure = plot_aimodel_response(aimodel_plotdata)
    assert isinstance(figure, Figure)


@enforce_types
def test_aimodel_factory_1var_varimps():
    _test_aimodel_factory_nvars_varimps(n=1)


@enforce_types
def test_aimodel_factory_2vars_varimps():
    _test_aimodel_factory_nvars_varimps(n=2)


@enforce_types
def test_aimodel_factory_3vars_varimps():
    _test_aimodel_factory_nvars_varimps(n=3)


@enforce_types
def test_aimodel_factory_4vars_varimps():
    _test_aimodel_factory_nvars_varimps(n=4)


@enforce_types
def test_aimodel_factory_5vars_varimps():
    _test_aimodel_factory_nvars_varimps(n=5)


@enforce_types
def test_aimodel_factory_10vars_varimps():
    _test_aimodel_factory_nvars_varimps(n=5)


@enforce_types
def test_aimodel_factory_25vars_varimps():
    _test_aimodel_factory_nvars_varimps(25)


@enforce_types
def test_aimodel_factory_100vars_varimps():
    _test_aimodel_factory_nvars_varimps(100)


@enforce_types
def _test_aimodel_factory_nvars_varimps(n: int):
    varnames = [f"x{i}" for i in range(n)]
    imps_avg = np.array([n - i + 1 for i in range(n)])
    assert imps_avg.shape[0] == n
    imps_stddev = imps_avg / 4.0
    _sum = sum(imps_avg)
    imps_avg = imps_avg / _sum
    imps_stddev = imps_stddev / _sum

    plot_data = Mock(spec=AimodelPlotdata)
    plot_data.model = Mock()
    plot_data.model.importance_per_var.return_value = (imps_avg, imps_stddev)
    plot_data.colnames = varnames

    figure = plot_aimodel_varimps(plot_data)
    assert isinstance(figure, Figure)
