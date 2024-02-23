from enforce_typing import enforce_types
import numpy as np
from numpy.testing import assert_array_equal

from pdr_backend.aimodel.aimodel import Aimodel

# this test file can stay thin, because most work is in test_aimodel_factory

@enforce_types
def test_aimodel():
    # [sample_i] : prediction_of_true_or_false
    ybool = np.array([True, True, False])

    # [sample_i][class_i]: prob_of_being_in_the_class
    T_0 = np.array([[0.9, 0.2], [0.8, 0.2], [0.3, 0.7]])
    T_1 = np.array([[0.2, 0.9], [0.2, 0.8], [0.7, 0.3]])

    # [sample_i] : prob_of_being_true
    yptrue = np.array([0.9, 0.8, 0.3])

    class MockSklearnModel:
        def __init__(self, class_i):
            self.class_i = class_i
            
        def fit(self, X, y):
            pass

        def predict(self, X):
            return ybool

        def predict_proba(self, X):
            # some sklearn classifiers treat class 0 as True class, others 1 (!)
            if self.class_i == 0:
                return T_0
            else:
                return T_1

    # for classifiers treating class 0 as True
    skm0 = MockSklearnModel(0)
    model = Aimodel(0, skm0)
    assert_array_equal(model.predict_true("foo"), ybool)
    assert_array_equal(model.predict_ptrue("bar"), yptrue)
    
    # for classifiers treating class 1 as True
    skm1 = MockSklearnModel(1)
    model = Aimodel(1, skm1)
    assert_array_equal(model.predict_true("foo"), ybool)
    assert_array_equal(model.predict_ptrue("bar"), yptrue)
