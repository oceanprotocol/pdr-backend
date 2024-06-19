import os

from enforce_typing import enforce_types
import pytest
from pytest import approx

from pdr_backend.aimodel.aimodel_data_factory import AimodelDataFactory
from pdr_backend.aimodel.aimodel_factory import AimodelFactory
from pdr_backend.aimodel.aimodel_plotdata import AimodelPlotdata
from pdr_backend.aimodel.aimodel_plotter import (
    plot_aimodel_response,
    plot_aimodel_varimps,
)
from pdr_backend.lake.merge_df import merge_rawohlcv_dfs
from pdr_backend.lake.test.resources import _df_from_raw_data
from pdr_backend.lake.test.resources2_btc import get_large_BINANCE_BTC_DATA
from pdr_backend.ppss.aimodel_data_ss import aimodel_data_ss_test_dict
from pdr_backend.ppss.aimodel_ss import aimodel_ss_test_dict
from pdr_backend.ppss.predictoor_ss import (
    PredictoorSS,
    predictoor_ss_test_dict,
)
from pdr_backend.statutil.dist_plotter import plot_dist
from pdr_backend.statutil.scoring import classif_acc


# set env variable as true to show plots
SHOW_PLOT = os.getenv("SHOW_PLOT", "false").lower() == "true"


# run a single test below with e.g.
# pytest pdr_backend/aimodel/test/test_aimodel_factory_btc.py::test_aimodel_btc_static[ClassifLinearRidge-1] # pylint: disable=line-too-long


@enforce_types
@pytest.mark.parametrize(
    "approach,autoregr_n,transform",
    [
        ("ClassifLinearRidge", 1, "None"),
        ("ClassifLinearRidge", 2, "None"),
        ("ClassifLinearRidge", 2, "RelDiff"),
        ("RegrLinearRidge", 1, "None"),
        ("RegrLinearRidge", 2, "None"),
        ("RegrLinearRidge", 2, "RelDiff"),
    ],
)
def test_aimodel_prices_static(approach: str, autoregr_n: int, transform: str):
    max_n_train = 200 # 5000 for manual testing
    pdr_ss = _get_predictoor_ss(approach, autoregr_n, max_n_train, transform)
    mergedohlcv_df = _get_btc_data()

    # create X, y, x_df
    data_f = AimodelDataFactory(pdr_ss)
    testshift = 0
    predict_feed = pdr_ss.predict_train_feedsets[0].predict
    train_feeds = pdr_ss.predict_train_feedsets[0].train_on
    X, ytran, _, x_df, _ = data_f.create_xy(
        mergedohlcv_df,
        testshift,
        predict_feed,
        train_feeds,
    )
    _assert_cols_ok(x_df, autoregr_n, transform)

    # create train/test data
    N_train = max_n_train - 100
    X_train, X_test = X[:N_train, :], X[N_train:, :]
    ytran_train, _ = ytran[:N_train], ytran[N_train:]
    y_thr = 0.0  # always 0.0 when modeling % change
    ytrue = data_f.ycont_to_ytrue(ytran, y_thr)
    ytrue_train, ytrue_test = ytrue[:N_train], ytrue[N_train:]

    # build model
    model_factory = AimodelFactory(pdr_ss.aimodel_ss)
    model = model_factory.build(X_train, ytrue_train, ytran_train, y_thr)

    # test model response
    ytrue_train_hat = model.predict_true(X_train)
    ytrue_test_hat = model.predict_true(X_test)
    train_acc = classif_acc(ytrue_train_hat, ytrue_train)
    test_acc = classif_acc(ytrue_test_hat, ytrue_test)
    assert 0.0 <= train_acc <= 1.0  # very loose
    assert 0.0 <= test_acc <= 1.0  # ""
    # print(f"train_acc={train_acc:.3f}, test_acc={test_acc:.3f}")

    _ = model.predict_ptrue(X)
    if model.do_regr:
        _ = model.predict_ycont(X)

    # plot model response
    sweep_vars = [0, 1]
    if autoregr_n == 1:
        sweep_vars = [0]
    plot_data = AimodelPlotdata(
        model,
        X,
        ytrue,
        ytran,
        y_thr,
        colnames=list(x_df.columns),
        slicing_x=X[-1, :],  # arbitrary
        sweep_vars=sweep_vars,
    )
    fig = plot_aimodel_response(plot_data)
    if SHOW_PLOT:
        fig.show()

    # test variable importances
    imps = model.importance_per_var()
    assert sum(imps) == approx(1.0, 0.01)

    # plot variable importances
    fig = plot_aimodel_varimps(plot_data)
    if SHOW_PLOT:
        fig.show()


@enforce_types
@pytest.mark.parametrize("transform", ["None", "RelDiff"])
def test_aimodel_prices_dynamic(transform: str):
    autoregr_n = 2
    max_n_train = 1000
    sim_test_n = 200
    yerrs = []
    for test_i in range(sim_test_n):
        # print(f"Iter #{test_i+1}/{sim_test_n}")
        yerr = _run_one_iter(
            autoregr_n, max_n_train, transform, sim_test_n, test_i,
        )
        yerrs.append(yerr)

    fig = plot_dist(yerrs, True, False, False)
    assert fig is not None
    if SHOW_PLOT:
        fig.show()


@enforce_types
def _run_one_iter(autoregr_n, max_n_train, transform, sim_test_n, test_i) \
        -> float:
    """@return -- yerr"""
    mergedohlcv_df = _get_btc_data()

    # mimic sim_engine::run_one_iter()
    approach = "RegrLinearRidge"
    pdr_ss = _get_predictoor_ss(approach, autoregr_n, max_n_train, transform)

    testshift = sim_test_n - test_i - 1  # eg [99, 98, .., 2, 1, 0]
    data_f = AimodelDataFactory(pdr_ss)
    predict_feed = pdr_ss.predict_train_feedsets[0].predict
    train_feeds = pdr_ss.predict_train_feedsets[0].train_on

    # X, ytran, and x_df are all expressed in % change wrt prev candle
    X, ytran, ysignal, _, _ = data_f.create_xy(
        mergedohlcv_df,
        testshift,
        predict_feed,
        train_feeds,
    )

    st_, fin = 0, X.shape[0] - 1
    X_train, X_test = X[st_:fin, :], X[fin : fin + 1, :]
    ytran_train, _ = ytran[st_:fin], ytran[fin : fin + 1]

    curprice = ysignal[-2]
    trueprice = ysignal[-1]

    y_thr = 0.0  # always 0.0 when modeling % change
    ytrue = data_f.ycont_to_ytrue(ytran, y_thr)
    ytrue_train, _ = ytrue[st_:fin], ytrue[fin : fin + 1]

    model_f = AimodelFactory(pdr_ss.aimodel_ss)
    model = model_f.build(X_train, ytrue_train, ytran_train, y_thr)

    # predict price direction
    prob_up: float = model.predict_ptrue(X_test)[0]  # in [0.0, 1.0]
    assert 0.0 <= prob_up <= 1.0  # very loose

    # update classifier metrics
    assert model.do_regr
    relchange = model.predict_ycont(X_test)[0]
    predprice = curprice + relchange * curprice
    yerr = trueprice - predprice

    s = f"prevprice={curprice:8.1f}"
    s += f", true_change={(trueprice-curprice)/(curprice)*100:9.5f}%"
    s += f", true_newprice={trueprice:8.1f}"
    s += "||"
    s += f" pred_change={relchange*100:9.5f}%"
    s += f", pred_newprice={predprice:9.1f}"
    s += "||"
    s += f" pred_price_err={yerr:9.3f}"
    print(s)

    return yerr


@enforce_types
def _assert_cols_ok(x_df, autoregr_n: int, transform:str):
    assert len(x_df.columns) == autoregr_n
    if autoregr_n != 2:
        return
    
    if transform == "None":
        target_x_df_columns = [
            "binanceus:BTC/USDT:close:z(t-3)",
            "binanceus:BTC/USDT:close:z(t-2)",
        ]
    else:
        target_x_df_columns = [
            "binanceus:BTC/USDT:close:(z(t-3)-z(t-4))/z(t-4)",
            "binanceus:BTC/USDT:close:(z(t-2)-z(t-3))/z(t-3)",
        ]
    assert list(x_df.columns) == target_x_df_columns


@enforce_types
def _get_predictoor_ss(
        approach: str, autoregr_n: int, max_n_train: int, transform: str,
) -> PredictoorSS:
    feedset_list = [
        {
            "predict": "binanceus BTC/USDT c 5m",
            "train_on": "binanceus BTC/USDT c 5m",
        },
    ]
    d = predictoor_ss_test_dict(
        feedset_list=feedset_list,
        aimodel_data_ss_dict=aimodel_data_ss_test_dict(
            max_n_train=max_n_train,
            autoregressive_n=autoregr_n,
            transform=transform,
        ),
        aimodel_ss_dict=aimodel_ss_test_dict(
            approach=approach,
            weight_recent="None",
            balance_classes="None",
            calibrate_probs="None",
            calibrate_regr="None",
        ),
    )
    return PredictoorSS(d)

_mergedohlcv_df = None

@enforce_types
def _get_btc_data():
    global _mergedohlcv_df
    if _mergedohlcv_df is not None:
        return _mergedohlcv_df
    rawohlcv_dfs = {
        "binanceus": {
            "BTC/USDT": _df_from_raw_data(get_large_BINANCE_BTC_DATA()),
        },
    }
    _mergedohlcv_df = merge_rawohlcv_dfs(rawohlcv_dfs)
    return _mergedohlcv_df
