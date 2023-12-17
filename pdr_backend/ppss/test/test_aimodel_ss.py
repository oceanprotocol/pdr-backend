from enforce_typing import enforce_types
import pytest

from pdr_backend.ppss.aimodel_ss import APPROACHES, AimodelSS


@enforce_types
def test_aimodel_ss1():
    d = {"approach": "LIN"}
    ss = AimodelSS(d)

    # yaml properties
    assert ss.approach == "LIN"

    # str
    assert "AimodelSS" in str(ss)
    assert "approach" in str(ss)


@enforce_types
def test_aimodel_ss2():
    for approach in APPROACHES:
        ss = AimodelSS({"approach": approach})
        assert approach in str(ss)

    with pytest.raises(ValueError):
        AimodelSS({"approach": "foo_approach"})
