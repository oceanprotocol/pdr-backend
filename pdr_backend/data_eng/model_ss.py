from enforce_typing import enforce_types

from pdr_backend.util.strutil import StrMixin

APPROACHES = ["LIN", "GPR", "SVR", "NuSVR", "LinearSVR"]


@enforce_types
class ModelSS(StrMixin):
    def __init__(self, model_approach: str):
        if model_approach not in APPROACHES:
            raise ValueError(model_approach)

        self.model_approach = model_approach
