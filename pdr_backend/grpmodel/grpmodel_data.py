from typing import Dict, List

from enforce_typing import enforce_types
import numpy as np

from pdr_backend.grpmodel.constants import Dirn, UP, DOWN


class GrpmodelData1Dir:

    @enforce_types
    def __init__(
        self,
        X: np.ndarray,
        ytrue: np.ndarray,
        colnames: List[str],
    ):
        assert len(X.shape) == 2
        assert len(ytrue.shape) == 1
        assert X.shape[0] == ytrue.shape[0], (X.shape[0], ytrue.shape[0])

        self.X: np.ndarray = X
        self.ytrue: np.ndarray = ytrue
        self.colnames: List[str] = colnames

    @property
    def st(self) -> int:
        return 0

    @property
    def fin(self) -> int:
        return self.X.shape[0] - 1

    @property
    def X_train(self) -> np.ndarray:
        return self.X[self.st : self.fin, :]

    @property
    def X_test(self) -> np.ndarray:
        return self.X[self.fin : self.fin + 1, :]

    @property
    def ytrue_train(self) -> np.ndarray:
        return self.ytrue[self.st : self.fin]


class GrpmodelData(dict):
    @enforce_types
    def __init__(
        self,
        data_UP: GrpmodelData1Dir,
        data_DOWN: GrpmodelData1Dir,
    ):
        self[UP] = data_UP
        self[DOWN] = data_DOWN

    @property
    def X_test(self) -> Dict[Dirn, np.ndarray]:
        return {UP: self[UP].X_test, DOWN: self[DOWN].X_test}
