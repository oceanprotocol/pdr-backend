from enforce_typing import enforce_types
import pytest

from pdr_backend.ppss.model_ss import APPROACHES, ModelSS


@enforce_types
def test_model_ss1():
    d = {"approach": "LIN"}
    ss = ModelSS(d)

    # yaml properties
    assert ss.approach == "LIN"

    # str
    assert "ModelSS" in str(ss)
    assert "approach" in str(ss)


@enforce_types
def test_model_ss2():
    for approach in APPROACHES:
        ss = ModelSS({"approach": approach})
        assert approach in str(ss)

    with pytest.raises(ValueError):
        ModelSS({"approach": "foo_approach"})
