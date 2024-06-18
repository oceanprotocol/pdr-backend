import os

from enforce_typing import enforce_types
import numpy as np
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
from pdr_backend.statutil.scoring import classif_acc

# set env variable as true to show plots
SHOW_PLOT = os.getenv("SHOW_PLOT", "false").lower() == "true"


# run a single test below with e.g.
# pytest pdr_backend/aimodel/test/test_aimodel_factory_btc.py::test_aimodel_btc[ClassifLinearRidge-1]


@enforce_types
@pytest.mark.parametrize(
    "approach,autoregressive_n",
    [
        ("ClassifLinearRidge", 1),
        ("RegrLinearRidge", 1),
        ("ClassifLinearRidge", 2),
        ("RegrLinearRidge", 2),
    ],
)
def test_aimodel_btc(approach: str, autoregressive_n: int):
    n = autoregressive_n
    N, N_train = 5000, 4900

    # create predictoor_ss
    feedset_list = [
        {
            "predict": "binanceus BTC/USDT c 5m",
            "train_on": "binanceus BTC/USDT c 5m",
        },
    ]
    d = predictoor_ss_test_dict(
        feedset_list=feedset_list,
        aimodel_data_ss_dict=aimodel_data_ss_test_dict(
            max_n_train=N,
            autoregressive_n=n,
        ),
        aimodel_ss_dict=aimodel_ss_test_dict(
            approach=approach,
            weight_recent="None",
            balance_classes="None",
            calibrate_probs="None",
            calibrate_regr="None",
        ),
    )
    predictoor_ss = PredictoorSS(d)

    # create mergedohlcv_df
    rawohlcv_dfs = {
        "binanceus": {
            "BTC/USDT": _df_from_raw_data(get_large_BINANCE_BTC_DATA()),
        },
    }
    mergedohlcv_df = merge_rawohlcv_dfs(rawohlcv_dfs)

    # create X, y, x_df
    aimodel_data_factory = AimodelDataFactory(predictoor_ss)
    testshift = 0
    predict_feed = predictoor_ss.predict_train_feedsets[0].predict
    train_feeds = predictoor_ss.predict_train_feedsets[0].train_on
    X, ycont, x_df, _ = aimodel_data_factory.create_xy(
        mergedohlcv_df,
        testshift,
        predict_feed,
        train_feeds,
    )

    # check columns
    assert len(x_df.columns) == n
    if n == 2:
        target_x_df_columns = [
            "binanceus:BTC/USDT:close:(z(t-3)-z(t-4))/z(t-4)",
            "binanceus:BTC/USDT:close:(z(t-2)-z(t-3))/z(t-3)",
        ]
        assert list(x_df.columns) == target_x_df_columns

    # create train/test data
    X_train, X_test = X[:N_train, :], X[N_train:, :]
    ycont_train, _ = ycont[:N_train], ycont[N_train:]
    y_thr = 0.0  # always 0.0 when modeling % change
    ytrue = aimodel_data_factory.ycont_to_ytrue(ycont, y_thr)
    ytrue_train, ytrue_test = ytrue[:N_train], ytrue[N_train:]

    # build model
    model_factory = AimodelFactory(predictoor_ss.aimodel_ss)
    model = model_factory.build(X_train, ytrue_train, ycont_train, y_thr)

    # test model response
    ytrue_train_hat = model.predict_true(X_train)
    ytrue_test_hat = model.predict_true(X_test)
    train_acc = classif_acc(ytrue_train_hat, ytrue_train)
    test_acc = classif_acc(ytrue_test_hat, ytrue_test)
    print(f"train_acc={train_acc:.3f}, test_acc={train_acc:.3f}")

    _ = model.predict_ptrue(X)
    if model.do_regr:
        _ = model.predict_ycont(X)

    # plot model response
    sweep_vars = [0, 1]
    if n == 1:
        sweep_vars = [0]
    plot_data = AimodelPlotdata(
        model,
        X,
        ytrue,
        ycont,
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
