from enforce_typing import enforce_types
import numpy as np
from numpy.test import assert_array_equal

from pdr_backend.aimodel.aimodel import Aimodel

# this test file can stay thin, because most work is in test_aimodel_factory

@enforce_types
def test_aimodel():
    # [sample_i] : prediction_of_true_or_false
    ybool = np.array([True, True, False])

    # [sample_i][class_i=0]: prob_of_being_true
    # [sample_i][class_i=1]: prob_of_being_false
    T = np.array([[0.9, 0.1], [0.8, 0.2], [0.3, 0.7]])

    # [sample_i] : prob_of_being_true
    yptrue = np.array([0.9, 0.8, 0.3])

    class MockSklearnModel:
        def fit(self, X, y):
            pass

        def predict(self, X):
            return ybool_hat

        def predict_prob(self, X):            
            return T

    skm = MockSklearnModel()
        
    m = Aimodel(skm)
    assert x._skm = skm

    assert_array_equal(x.predict("foo"), ybool)
    assert_array_equal(x.predict_ptrue("bar"), yptrue)
