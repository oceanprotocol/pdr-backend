from unittest.mock import Mock

from enforce_typing import enforce_types
import numpy as np

from pdr_backend.binmodel.constants import UP, DOWN
from pdr_backend.aimodel.aimodel import Aimodel
from pdr_backend.binmodel.binmodel import Binmodel


@enforce_types
def test_binmodel():
    model_UP = Mock(spec=Aimodel)
    model_UP.predict_ptrue = Mock(return_value=np.array([0.2]))

    model_DOWN = Mock(spec=Aimodel)
    model_DOWN.predict_ptrue = Mock(return_value=np.array([0.8]))
    model = Binmodel(model_UP, model_DOWN)

    X_test = {UP: np.array([[1.0]]), DOWN: np.array([[2.0]])}

    predprob = model.predict_next(X_test)
    assert predprob == {UP: 0.2, DOWN: 0.8}
