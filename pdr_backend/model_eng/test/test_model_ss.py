from enforce_typing import enforce_types
import pytest

from pdr_backend.model_eng.model_ss import APPROACHES, ModelSS


@enforce_types
def test_model_ss1():
    ss = ModelSS("LIN")
    assert ss.model_approach == "LIN"

    assert "ModelSS" in str(ss)
    assert "model_approach" in str(ss)


@enforce_types
def test_model_ss2():
    for approach in APPROACHES:
        ss = ModelSS(approach)
        assert approach in str(ss)

    with pytest.raises(ValueError):
        ModelSS("foo_approach")
