from enforce_typing import enforce_types
import numpy as np

from pdr_backend.sim.constants import UP, DOWN

@enforce_types
class SimModelData(dict):
    def __init__(
        self,
        data_UP: SimModelData1Dir,
        data_DOWN: SimModelData1Dir,
    ):
        self[UP] = data_UP
        self[DOWN] = data_DOWN

class SimModelData1Dir:
    
    @enforce_types
    def __init__(self, X: np.ndarray, ytrue: np.ndarray):        
        self.X: np.ndarray = X
        self.ytrue: np.ndarray = ytrue
        
    @property
    def st(self) -> int:
        return 0
    
    @property
    def fin(self) -> int:
        return self.X.shape[0] - 1

    @property
    def X_train(self) -> np.ndarray:
        return self.X[self.st:self.fin, :]

    @property
    def X_test(self) -> np.ndarray:
        return self.X[self.fin : self.fin + 1, :]
    
    @property
    def ytrue_train(self) -> List[bool]:
        return self.ytrue[self.st:self.fin]
    
