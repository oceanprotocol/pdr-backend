#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enforce_typing import enforce_types
import pytest

from pdr_backend.ppss.aimodel_ss import (
    AimodelSS,
    aimodel_ss_test_dict,
    APPROACH_OPTIONS,
    CALIBRATE_PROBS_OPTIONS,
    CALIBRATE_REGR_OPTIONS,
    BALANCE_CLASSES_OPTIONS,
    REGR_APPROACH_OPTIONS,
    WEIGHT_RECENT_OPTIONS,
)


@enforce_types
def test_aimodel_ss__default_values():
    d = aimodel_ss_test_dict()
    ss = AimodelSS(d)

    assert ss.approach == d["approach"] == "ClassifLinearRidge"
    assert ss.weight_recent == d["weight_recent"] == "10x_5x"
    assert ss.weight_recent_n == (10, 5)
    assert ss.balance_classes == d["balance_classes"] == "SMOTE"
    assert (
        ss.calibrate_probs == d["calibrate_probs"] == "CalibratedClassifierCV_Sigmoid"
    )
    assert ss.calibrate_regr == d["calibrate_regr"] == "None"

    # str
    assert "AimodelSS" in str(ss)
    assert "approach" in str(ss)
    assert not ss.do_regr


@enforce_types
def test_aimodel_ss__nondefault_values():
    d = aimodel_ss_test_dict()
    ss = AimodelSS(d)

    for approach in APPROACH_OPTIONS:
        ss = AimodelSS(aimodel_ss_test_dict(approach=approach))
        assert ss.approach == approach and approach in str(ss)

        do_regr = approach in REGR_APPROACH_OPTIONS
        assert ss.do_regr == do_regr

    for weight_recent in WEIGHT_RECENT_OPTIONS:
        ss = AimodelSS(aimodel_ss_test_dict(weight_recent=weight_recent))
        assert ss.weight_recent == weight_recent and weight_recent in str(ss)
        if ss.weight_recent == "10x_5x":
            assert ss.weight_recent_n == (10, 5)
        if ss.weight_recent == "10000x":
            assert ss.weight_recent_n == (10000, 0)

    for balance_classes in BALANCE_CLASSES_OPTIONS:
        ss = AimodelSS(aimodel_ss_test_dict(balance_classes=balance_classes))
        assert ss.balance_classes == balance_classes and balance_classes in str(ss)

    for calibrate_probs in CALIBRATE_PROBS_OPTIONS:
        ss = AimodelSS(aimodel_ss_test_dict(calibrate_probs=calibrate_probs))
        assert ss.calibrate_probs == calibrate_probs and calibrate_probs in str(ss)

    for calibrate_regr in CALIBRATE_REGR_OPTIONS:
        ss = AimodelSS(aimodel_ss_test_dict(calibrate_regr=calibrate_regr))
        assert ss.calibrate_regr == calibrate_regr and calibrate_regr in str(ss)


@enforce_types
def test_aimodel_ss__bad_inputs():

    with pytest.raises(ValueError):
        AimodelSS(aimodel_ss_test_dict(approach="foo"))

    with pytest.raises(ValueError):
        AimodelSS(aimodel_ss_test_dict(weight_recent="foo"))

    with pytest.raises(ValueError):
        AimodelSS(aimodel_ss_test_dict(balance_classes="foo"))

    with pytest.raises(ValueError):
        AimodelSS(aimodel_ss_test_dict(calibrate_probs="foo"))

    with pytest.raises(ValueError):
        AimodelSS(aimodel_ss_test_dict(calibrate_regr="foo"))


@enforce_types
def test_aimodel_ss__calibrate_probs_skmethod():
    d = aimodel_ss_test_dict(calibrate_probs="CalibratedClassifierCV_Sigmoid")
    ss = AimodelSS(d)
    assert ss.calibrate_probs_skmethod(100) == "sigmoid"
    assert ss.calibrate_probs_skmethod(1000) == "sigmoid"

    d = aimodel_ss_test_dict(calibrate_probs="CalibratedClassifierCV_Isotonic")
    ss = AimodelSS(d)
    assert ss.calibrate_probs_skmethod(100) == "sigmoid"  # because N is small
    assert ss.calibrate_probs_skmethod(1000) == "isotonic"
