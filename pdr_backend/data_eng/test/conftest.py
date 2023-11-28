import pytest

from pdr_backend.data_eng.model_factory import ModelFactory
from pdr_backend.ppss.model_ss import ModelSS


@pytest.fixture(scope="session")
def model_factory():
    model_ss = ModelSS({"approach": "LIN"})
    return ModelFactory(model_ss)
