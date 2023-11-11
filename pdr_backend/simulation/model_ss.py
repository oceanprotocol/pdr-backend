from enforce_typing import enforce_types

from pdr_backend.util.strutil import StrMixin


@enforce_types
class ModelSS(StrMixin):
    def __init__(
        self,
        model_approach: str,  # LIN,GPR,SVR,NuSVR,LinearSVR
    ):
        self.model_approach = model_approach
