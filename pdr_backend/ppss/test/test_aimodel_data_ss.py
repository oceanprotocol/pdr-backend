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
    assert ss.autoregressive_n == d["max_diff"] == 0

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
    
    ss = AimodelDataSS(aimodel_data_ss_test_dict(max_diff=2))
    assert ss.max_diff == 2


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
        AimodelDataSS(aimodel_data_ss_test_dict(max_diff=-1))
        
    with pytest.raises(ValueError):
        AimodelDataSS(aimodel_data_ss_test_dict(max_diff=3))

    with pytest.raises(TypeError):
        AimodelDataSS(aimodel_data_ss_test_dict(max_diff=0.1))
        
    with pytest.raises(TypeError):
        AimodelDataSS(aimodel_data_ss_test_dict(max_diff=np.inf))
