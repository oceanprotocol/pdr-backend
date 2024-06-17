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
    assert ss.do_diff0 == d["do_diff0"] == True
    assert ss.do_diff1 == d["do_diff1"] == False
    assert ss.do_diff2 == d["do_diff2"] == False

    # str
    assert "AimodelDataSS" in str(ss)
    assert "max_n_train" in str(ss)

    # derived
    assert ss.num_diffs == 1
    assert ss.max_diff == 0


@enforce_types
def test_aimodel_data_ss__nondefault_values():
    d = aimodel_data_ss_test_dict()
    ss = AimodelDataSS(d)

    ss = AimodelDataSS(aimodel_data_ss_test_dict(max_n_train=39))
    assert ss.max_n_train == 39

    ss = AimodelDataSS(aimodel_data_ss_test_dict(autoregressive_n=13))
    assert ss.autoregressive_n == 13

    ss = AimodelDataSS(aimodel_data_ss_test_dict(do_diff0=False, do_diff1=True))
    assert not ss.do_diff0 and ss.do_diff1 and not ss.do_diff2
    assert ss.num_diffs == 1
    assert ss.max_diff == 1

    ss = AimodelDataSS(aimodel_data_ss_test_dict(do_diff0=False, do_diff2=True))
    assert not ss.do_diff0 and not ss.do_diff1 and ss.do_diff2
    assert ss.num_diffs == 1
    assert ss.max_diff == 2

    ss = AimodelDataSS(aimodel_data_ss_test_dict(do_diff1=True))
    assert ss.num_diffs == 2
    assert ss.max_diff == 1
    
    ss = AimodelDataSS(aimodel_data_ss_test_dict(do_diff2=True))
    assert ss.num_diffs == 2
    assert ss.max_diff == 2
    
    ss = AimodelDataSS(aimodel_data_ss_test_dict(do_diff1=True, do_diff2=True))
    assert ss.do_diff0 and ss.do_diff1 and ss.do_diff2
    assert ss.num_diffs == 3
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
        AimodelDataSS(aimodel_data_ss_test_dict(
            do_diff0=False,do_diff1=False,do_diff2=False
        ))

    with pytest.raises(TypeError):
        AimodelDataSS(aimodel_data_ss_test_dict(do_diff0="foo"))
        
    with pytest.raises(TypeError):
        AimodelDataSS(aimodel_data_ss_test_dict(do_diff1="foo"))
        
    with pytest.raises(TypeError):
        AimodelDataSS(aimodel_data_ss_test_dict(do_diff2="foo"))

