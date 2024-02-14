import copy

import numpy as np
from enforce_typing import enforce_types

from pdr_backend.ppss.model_ss import BaseModelSS

APPROACHES = ["LIN", "GPR", "SVR", "NuSVR", "LinearSVR"]


@enforce_types
class RegressionModelSS(BaseModelSS):
    @enforce_types
    def copy(self):
        d2 = copy.deepcopy(self.d)

        return RegressionModelSS(d2)
