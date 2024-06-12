import numpy as np
from enforce_typing import enforce_types

from pdr_backend.statutil.scoring import classif_acc


@enforce_types
def test_classif_acc():
    ybool = np.array([True, True, False, True])

    ybool_hat = np.array([True, True, False, True])
    assert classif_acc(ybool_hat, ybool) == 1.0

    ybool_hat = np.array([False, False, True, False])
    assert classif_acc(ybool_hat, ybool) == 0.0

    ybool_hat = np.array([True, False, False, True])
    assert classif_acc(ybool_hat, ybool) == 0.75
