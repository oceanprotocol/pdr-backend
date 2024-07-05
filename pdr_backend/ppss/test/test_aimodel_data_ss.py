#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enforce_typing import enforce_types
import numpy as np
import pytest

from pdr_backend.ppss.aimodel_data_ss import (
    AimodelDataSS,
    aimodel_data_ss_test_dict,
)


@enforce_types
def test_aimodel_data_ss__default_values():
    d = aimodel_data_ss_test_dict()
    ss = AimodelDataSS(d)

    assert ss.max_n_train == d["max_n_train"] == 7
    assert ss.autoregressive_n == d["autoregressive_n"] == 3
    assert ss.transform == d["transform"] == "None"

    # str
    assert "AimodelDataSS" in str(ss)
    assert "max_n_train" in str(ss)


@enforce_types
def test_aimodel_data_ss__nondefault_values():
    d = aimodel_data_ss_test_dict()
    ss = AimodelDataSS(d)

    ss = AimodelDataSS(aimodel_data_ss_test_dict(max_n_train=39))
    assert ss.max_n_train == 39

    ss = AimodelDataSS(aimodel_data_ss_test_dict(autoregressive_n=13))
    assert ss.autoregressive_n == 13

    ss = AimodelDataSS(aimodel_data_ss_test_dict(transform="RelDiff"))
    assert ss.transform == "RelDiff"


@enforce_types
def test_aimodel_data_ss__bad_inputs():
    with pytest.raises(ValueError):
        AimodelDataSS(aimodel_data_ss_test_dict(max_n_train=0))

    with pytest.raises(TypeError):
        AimodelDataSS(aimodel_data_ss_test_dict(max_n_train=3.1))

    with pytest.raises(ValueError):
        AimodelDataSS(aimodel_data_ss_test_dict(autoregressive_n=0))

    with pytest.raises(TypeError):
        AimodelDataSS(aimodel_data_ss_test_dict(autoregressive_n=3.1))

    with pytest.raises(TypeError):
        AimodelDataSS(aimodel_data_ss_test_dict(autoregressive_n=np.inf))

    with pytest.raises(ValueError):
        AimodelDataSS(aimodel_data_ss_test_dict(transform="foo"))

    with pytest.raises(TypeError):
        AimodelDataSS(aimodel_data_ss_test_dict(transform=3.1))


@enforce_types
def test_aimodel_data_ss__setters():
    d = aimodel_data_ss_test_dict()
    ss = AimodelDataSS(d)

    # max_n_train
    ss.set_max_n_train(32)
    assert ss.max_n_train == 32
    with pytest.raises(ValueError):
        ss.set_max_n_train(0)
    with pytest.raises(ValueError):
        ss.set_max_n_train(-5)

    # autoregressive_n
    ss.set_autoregressive_n(12)
    assert ss.autoregressive_n == 12
    with pytest.raises(ValueError):
        ss.set_autoregressive_n(0)
    with pytest.raises(ValueError):
        ss.set_autoregressive_n(-5)

    # transform
    ss.set_transform("RelDiff")
    assert ss.transform == "RelDiff"
    with pytest.raises(ValueError):
        ss.set_transform("foo")
