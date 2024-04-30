from enforce_typing import enforce_types
import numpy as np
import pytest

from pdr_backend.ppss.aimodel_ss import (
    AimodelSS,
    aimodel_ss_test_dict,
    APPROACH_OPTIONS,
    CALIBRATE_PROBS_OPTIONS,
    BALANCE_CLASSES_OPTIONS,
    WEIGHT_RECENT_OPTIONS,
)


@enforce_types
def test_aimodel_ss__default_values():
    d = aimodel_ss_test_dict()
    ss = AimodelSS(d)

    assert ss.max_n_train == d["max_n_train"] == 7
    assert ss.autoregressive_n == d["autoregressive_n"] == 3

    assert ss.approach == d["approach"] == "LinearLogistic"
    assert ss.weight_recent == d["weight_recent"] == "10x_5x"
    assert ss.balance_classes == d["balance_classes"] == "SMOTE"
    assert (
        ss.calibrate_probs == d["calibrate_probs"] == "CalibratedClassifierCV_Sigmoid"
    )

    # str
    assert "AimodelSS" in str(ss)
    assert "approach" in str(ss)


@enforce_types
def test_aimodel_ss__nondefault_values():
    d = aimodel_ss_test_dict()
    ss = AimodelSS(d)

    ss = AimodelSS(aimodel_ss_test_dict(max_n_train=39))
    assert ss.max_n_train == 39

    ss = AimodelSS(aimodel_ss_test_dict(autoregressive_n=13))
    assert ss.autoregressive_n == 13

    for approach in APPROACH_OPTIONS:
        ss = AimodelSS(aimodel_ss_test_dict(approach=approach))
        assert ss.approach == approach and approach in str(ss)

    for weight_recent in WEIGHT_RECENT_OPTIONS:
        ss = AimodelSS(aimodel_ss_test_dict(weight_recent=weight_recent))
        assert ss.weight_recent == weight_recent and weight_recent in str(ss)

    for balance_classes in BALANCE_CLASSES_OPTIONS:
        ss = AimodelSS(aimodel_ss_test_dict(balance_classes=balance_classes))
        assert ss.balance_classes == balance_classes and balance_classes in str(ss)

    for calibrate_probs in CALIBRATE_PROBS_OPTIONS:
        ss = AimodelSS(aimodel_ss_test_dict(calibrate_probs=calibrate_probs))
        assert ss.calibrate_probs == calibrate_probs and calibrate_probs in str(ss)


@enforce_types
def test_aimodel_ss__bad_inputs():
    with pytest.raises(ValueError):
        AimodelSS(aimodel_ss_test_dict(max_n_train=0))

    with pytest.raises(TypeError):
        AimodelSS(aimodel_ss_test_dict(max_n_train=3.1))

    with pytest.raises(ValueError):
        AimodelSS(aimodel_ss_test_dict(autoregressive_n=0))

    with pytest.raises(TypeError):
        AimodelSS(aimodel_ss_test_dict(autoregressive_n=3.1))

    with pytest.raises(TypeError):
        AimodelSS(aimodel_ss_test_dict(autoregressive_n=np.inf))

    with pytest.raises(ValueError):
        AimodelSS(aimodel_ss_test_dict(approach="foo"))

    with pytest.raises(ValueError):
        AimodelSS(aimodel_ss_test_dict(weight_recent="foo"))

    with pytest.raises(ValueError):
        AimodelSS(aimodel_ss_test_dict(balance_classes="foo"))

    with pytest.raises(ValueError):
        AimodelSS(aimodel_ss_test_dict(calibrate_probs="foo"))


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
