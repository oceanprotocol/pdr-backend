from enforce_typing import enforce_types
import numpy as np
from numpy.testing import assert_array_equal

from pdr_backend.aimodel.ycont_to_ytrue import ycont_to_ytrue


@enforce_types
def test_ycont_to_ytrue():
    ycont = np.array([8.3, 6.4, 7.5, 8.6, 5.0])
    y_thr = 7.0
    target_ybool = np.array([True, False, True, True, False])
    ybool = ycont_to_ytrue(ycont, y_thr)
    assert_array_equal(ybool, target_ybool)
