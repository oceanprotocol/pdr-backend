from enforce_typing import enforce_types

from pdr_backend.util.strutil import StrMixin

APPROACHES = ["LIN", "GPR", "SVR", "NuSVR", "LinearSVR"]


@enforce_types
class ModelSS(StrMixin):
    __STR_OBJDIR__ = ["d"]

    def __init__(self, d: dict):
        self.d = d  # yaml_dict["model_ss"]

        # test inputs
        if self.approach not in APPROACHES:
            raise ValueError(self.approach)

    # --------------------------------
    # yaml properties
    @property
    def approach(self) -> str:
        return self.d["approach"]  # eg "LIN"
