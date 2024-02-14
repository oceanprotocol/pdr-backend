import copy

import numpy as np
from enforce_typing import enforce_types

from pdr_backend.ppss.model_ss import BaseModelSS


APPROACHES = ["LIN"]


@enforce_types
class ClassifierModelSS(BaseModelSS):
    @property
    def approach(self) -> str:
        return "LIN"

    @enforce_types
    def copy(self):
        d2 = copy.deepcopy(self.d)

        return ClassifierModelSS(d2)
