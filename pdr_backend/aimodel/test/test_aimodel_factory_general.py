#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from unittest.mock import Mock
import os
import numpy as np

from enforce_typing import enforce_types
from numpy.testing import assert_array_equal
from plotly.graph_objs._figure import Figure
import pytest
from pytest import approx

from pdr_backend.aimodel.aimodel_factory import AimodelFactory
from pdr_backend.aimodel.aimodel_plotdata import AimodelPlotdata
from pdr_backend.aimodel.aimodel_plotter import (
    plot_aimodel_response,
    plot_aimodel_varimps,
)
from pdr_backend.aimodel.ycont_to_ytrue import ycont_to_ytrue
from pdr_backend.ppss.aimodel_ss import (
    AimodelSS,
    aimodel_ss_test_dict,
    APPROACH_OPTIONS,
)
from pdr_backend.statutil.scoring import classif_acc

# set env variable as true to show plots
SHOW_PLOT = os.getenv("SHOW_PLOT", "false").lower() == "true"


@enforce_types
@pytest.mark.parametrize(
    "approach,func",
    [
        ("ClassifLinearRidge", "lin"),
        ("ClassifGaussianProcess", "nonlin"),
        ("ClassifXgboost", "nonlin"),
        ("RegrLinearRidge", "lin"),
        ("RegrGaussianProcess", "nonlin"),
        ("RegrXgboost", "nonlin"),
    ],
)
def test_aimodel_1var(approach: str, func: str):
    """1 input var. It will plot that var on both axes"""
    # settings, factory
    ss = AimodelSS(aimodel_ss_test_dict(approach=approach))
    factory = AimodelFactory(ss)

    # data
    N = 50
    mn, mx = -10.0, +10.0
    X = np.random.uniform(mn, mx, (N, 1))
    if func == "lin":
        ycont = 3.0 + 4.0 * X[:, 0]
    else:
        ycont = 3.0 + 4.0 * X[:, 0] + 0.3 * (X[:, 0] - 3) ** 2
    y_thr = np.average(ycont)  # avg gives good class balance
    ytrue = ycont > y_thr

    # build model
    model = factory.build(X, ytrue, ycont, y_thr, show_warnings=False)

    # test variable importances
    imps = model.importance_per_var()
    assert_array_equal(imps, np.array([1.0]))

    # plot response: always classifier, and regressor if relevant
    colnames = ["x0"]
    slicing_x = np.array([0.1])  # arbitrary
    sweep_vars = [0]
    aimodel_plotdata = AimodelPlotdata(
        model,
        X,
        ytrue,
        ycont,
        y_thr,
        colnames,
        slicing_x,
        sweep_vars,
    )
    figure = plot_aimodel_response(aimodel_plotdata)
    assert isinstance(figure, Figure)
    if SHOW_PLOT:
        figure.show()


@enforce_types
@pytest.mark.parametrize("approach", APPROACH_OPTIONS)
def test_aimodel_2vars(approach: str):
    # settings, factory
    ss = AimodelSS(aimodel_ss_test_dict(approach=approach))
    factory = AimodelFactory(ss)

    # data
    N = 1000
    mn, mx = -10.0, +10.0
    X = np.random.uniform(mn, mx, (N, 2))
    ycont = 3.0 + 1.0 * X[:, 0] + 2.0 * X[:, 1]  # ycont = 3 + 1*x0 + 2*x1
    y_thr = 2.0
    ytrue = ycont > y_thr

    # build model, with all data in
    model = factory.build(X, ytrue, ycont, y_thr, show_warnings=False)
    assert model.do_regr == ss.do_regr

    # test predict_true() & predict_ptrue()
    ytrue_hat = model.predict_true(X)
    yptrue_hat = model.predict_ptrue(X)

    assert ytrue_hat.shape == yptrue_hat.shape == (N,)
    assert ytrue_hat.dtype == bool
    assert yptrue_hat.dtype == float

    if approach not in ["ClassifConstant", "RegrConstant"]:
        assert classif_acc(ytrue_hat, ytrue) > 0.8
        assert 0 <= min(yptrue_hat) <= max(yptrue_hat) <= 1.0
    assert_array_equal(yptrue_hat > 0.5, ytrue_hat)

    # test build model, with minimal data in
    if ss.do_regr:
        _ = factory.build(X, None, ycont, y_thr, show_warnings=False)
    else:
        _ = factory.build(X, ytrue, None, None, show_warnings=False)

    # test variable importances
    imps = model.importance_per_var()
    assert sum(imps) == approx(1.0, 0.01)
    assert imps[0] == approx(0.333, abs=0.3)
    assert imps[1] == approx(0.667, abs=0.3)

    # plot model response
    colnames = ["x0", "x1"]
    slicing_x = np.array([0.0, 1.0])  # arbitrary
    sweep_vars = [0, 1]
    d = AimodelPlotdata(
        model,
        X,
        ytrue,
        ycont,
        y_thr,
        colnames,
        slicing_x,
        sweep_vars,
    )
    fig = plot_aimodel_response(d)
    assert isinstance(fig, Figure)
    if SHOW_PLOT:
        fig.show()

    # test predict_ycont()
    if not model.do_regr:
        return
    ycont_hat = model.predict_ycont(X)
    assert ycont_hat.shape == (N,)
    assert ycont_hat.dtype == float


@enforce_types
def test_aimodel_can_ClassifConstant_emerge():
    d = aimodel_ss_test_dict(
        approach="ClassifLinearRidge",
        weight_recent="None",
    )
    ss = AimodelSS(d)
    assert not ss.do_regr
    factory = AimodelFactory(ss)

    N = 1000
    X = np.random.uniform(-10.0, +10.0, (N, 2))

    ytrue = np.full((N,), True)
    model = factory.build(X, ytrue)
    assert not model.do_regr
    assert_array_equal(model.predict_true(X), np.full((N,), True))
    assert_array_equal(model.predict_ptrue(X), np.full((N,), 1.0))

    ytrue = np.full((N,), False)
    model = factory.build(X, ytrue)
    assert not model.do_regr
    assert_array_equal(model.predict_true(X), np.full((N,), False))
    assert_array_equal(model.predict_ptrue(X), np.full((N,), 0.0))


@enforce_types
def test_aimodel_can_RegrConstant_emerge():
    d = aimodel_ss_test_dict(
        approach="RegrLinearLS",
        weight_recent="None",
    )
    ss = AimodelSS(d)
    assert ss.do_regr
    factory = AimodelFactory(ss)

    N = 1000
    X = np.random.uniform(-10.0, +10.0, (N, 2))

    ytrue = None  # shouldn't need to fill this
    ycont = 3.0 * np.ones(N, dtype=float)

    y_thr = 2.0
    model = factory.build(X, ytrue, ycont, y_thr)
    assert model.do_regr
    assert_array_equal(model.predict_ycont(X), np.full((N,), 3.0))
    assert_array_equal(model.predict_true(X), np.full((N,), True))
    assert_array_equal(model.predict_ptrue(X), np.full((N,), 1.0))

    y_thr = 4.0
    model = factory.build(X, ytrue, ycont, y_thr)
    assert model.do_regr
    assert_array_equal(model.predict_ycont(X), np.full((N,), 3.0))
    assert_array_equal(model.predict_true(X), np.full((N,), False))
    assert_array_equal(model.predict_ptrue(X), np.full((N,), 0.0))


@enforce_types
def test_aimodel_classif_accuracy():
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
    ytrue_trn = ycont_to_ytrue(ycont_trn, y_thr)

    model = aimodel_factory.build(X_trn, ytrue_trn)

    ytrue_trn_hat = model.predict_true(X_trn)
    assert_array_equal(ytrue_trn, ytrue_trn_hat)  # expect zero error

    yptrue_trn_hat = model.predict_ptrue(X_trn)
    assert_array_equal(yptrue_trn_hat > 0.5, ytrue_trn_hat)


@enforce_types
@pytest.mark.parametrize("approach", ["ClassifLinearRidge", "RegrLinearRidge"])
def test_aimodel_5varmodel_lineplot(approach: str):
    """5 input vars; sweep 1 var."""
    # settings, factory
    ss = AimodelSS(aimodel_ss_test_dict(approach=approach))
    factory = AimodelFactory(ss)

    # data
    N = 1000
    mn, mx = -10.0, +10.0
    X = np.random.uniform(mn, mx, (N, 5))
    ycont = (
        10.0
        + 0.1 * X[:, 0]
        + 1.0 * X[:, 1]
        + 2.0 * X[:, 2]
        + 3.0 * X[:, 3]
        + 4.0 * X[:, 4]
    )
    y_thr = np.average(ycont)  # avg gives good class balance
    ytrue = ycont > y_thr

    # build model
    model = factory.build(X, ytrue, ycont, y_thr, show_warnings=False)

    # test variable importances
    imps = model.importance_per_var()
    assert len(imps) == 5
    assert imps[0] < imps[1] < imps[2] < imps[3] < imps[4]

    # plot
    colnames = ["x0", "x1", "x2", "x3", "x4"]
    slicing_x = np.array([0.1] * 5)  # arbitrary
    sweep_vars = [2]  # x2
    aimodel_plotdata = AimodelPlotdata(
        model,
        X,
        ytrue,
        ycont,
        y_thr,
        colnames,
        slicing_x,
        sweep_vars,
    )
    figure = plot_aimodel_response(aimodel_plotdata)
    assert isinstance(figure, Figure)

    if SHOW_PLOT:
        figure.show()


@enforce_types
@pytest.mark.parametrize(
    "approach,target_n_classes",
    [
        ("ClassifLinearRidge", 1),
        ("ClassifLinearRidge", 2),
        ("RegrLinearRidge", 1),
        ("RegrLinearRidge", 2),
    ],
)
def test_aimodel_4vars_response(approach: str, target_n_classes: int):
    """4 input vars. It will plot the 2 most important vars."""
    assert target_n_classes in [1, 2]

    # settings, factory
    ss = AimodelSS(aimodel_ss_test_dict(approach=approach))
    factory = AimodelFactory(ss)

    # data
    N = 1000
    mn, mx = -10.0, +10.0
    X = np.random.uniform(mn, mx, (N, 4))
    ycont = 3.0 + 4.0 * X[:, 0] + 3.0 * X[:, 1] + 2.0 * X[:, 2] + 1.0 * X[:, 3]
    if target_n_classes == 2:
        y_thr = np.average(ycont)  # avg gives good class balance
    else:
        y_thr = 1000.0
    ytrue = ycont > y_thr
    colnames = ["x0", "x1", "x3", "x4"]

    # build model
    model = factory.build(X, ytrue, ycont, y_thr, show_warnings=False)

    # test variable importances
    imps = model.importance_per_var()
    if model.do_regr or target_n_classes == 2:  # expect sane var impacts
        assert imps[0] > imps[1] > imps[2] > imps[3] > 0.0
        assert sum(imps) == approx(1.0, 0.01)
        assert imps[0] == approx(4.0 / 10.0, abs=0.2)
        assert imps[1] == approx(3.0 / 10.0, abs=0.2)
        assert imps[2] == approx(2.0 / 10.0, abs=0.2)
        assert imps[3] == approx(1.0 / 10.0, abs=0.2)
    else:
        assert min(imps) == max(imps) == 0.25

    # plot model response
    slicing_x = np.array([0.1, 1.0, 2.0, 3.0])  # arbitrary
    sweep_vars = [0, 1]
    aimodel_plotdata = AimodelPlotdata(
        model,
        X,
        ytrue,
        ycont,
        y_thr,
        colnames,
        slicing_x,
        sweep_vars,
    )

    figure = plot_aimodel_response(aimodel_plotdata)
    assert isinstance(figure, Figure)

    if SHOW_PLOT:
        figure.show()


@enforce_types
@pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 10, 25, 100])
def test_aimodel_nvars_varimps(n: int):
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

    if SHOW_PLOT:
        figure.show()


@enforce_types
@pytest.mark.parametrize("approach", ["RegrLinearRidge", "RegrConstant"])
def test_aimodel__regr_0error__via_10000x(approach):
    d = aimodel_ss_test_dict(
        approach=approach,
        weight_recent="10000x",  # main setting
        balance_classes="None",
        calibrate_probs="None",
        calibrate_regr="None",  # explicitly None here
    )
    for curprice_xval in [-8, -5, -2, 2, 5, 8]:
        _test_aimodel__regr_0error(d, curprice_xval)


@enforce_types
@pytest.mark.parametrize("approach", ["RegrLinearRidge", "RegrConstant"])
def test_aimodel__regr_0error__via_calibrate_regr(approach):
    d = aimodel_ss_test_dict(
        approach=approach,
        weight_recent="None",  # explicitly None here
        balance_classes="None",
        calibrate_probs="None",
        calibrate_regr="CurrentYval",  # main setting
    )
    for curprice_xval in [-8, -5, -2, 2, 5, 8]:
        _test_aimodel__regr_0error(d, curprice_xval)


@enforce_types
def _test_aimodel__regr_0error(d: dict, curprice_xval):
    """Want regressor to have near-zero error at current price. See #1213"""
    ss = AimodelSS(d)
    if "constant" in ss.approach.lower():
        return
    factory = AimodelFactory(ss)

    # X/y data
    N = 50
    x = np.random.uniform(-10, +10, (N,))
    x[-1] = curprice_xval
    ycont = 3.0 + 4.0 * x + 1.0 * x**2
    X = np.reshape(x, (N, 1))
    y_thr = 1.0  # arbitrary
    ytrue = ycont > y_thr

    # build model
    model = factory.build(X, ytrue, ycont, y_thr, show_warnings=False)

    # is error at current near-zero?
    yhat = model.predict_ycont(X)
    err = abs(ycont[-1] - yhat[-1]) / np.std(ycont)
    assert abs(err) < 0.1, err

    # plot response
    colnames = ["x0"]
    slicing_x = np.array([0.1])  # arbitrary
    sweep_vars = [0]
    aimodel_plotdata = AimodelPlotdata(
        model,
        X,
        ytrue,
        ycont,
        y_thr,
        colnames,
        slicing_x,
        sweep_vars,
    )
    figure = plot_aimodel_response(aimodel_plotdata)
    assert isinstance(figure, Figure)
    if SHOW_PLOT:
        figure.show()
