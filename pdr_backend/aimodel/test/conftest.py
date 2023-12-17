from enforce_typing import enforce_types
import pytest

from pdr_backend.aimodel.aimodel_factory import AimodelFactory
from pdr_backend.ppss.model_ss import ModelSS

@enforce_types
@pytest.fixture()
def aimodel_factory():
    model_ss = ModelSS({"approach": "LIN"})
    return AimodelFactory(model_ss)

