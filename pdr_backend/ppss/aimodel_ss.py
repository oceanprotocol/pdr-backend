from enforce_typing import enforce_types

from pdr_backend.util.strutil import StrMixin

APPROACHES = ["LIN", "GPR", "SVR", "NuSVR", "LinearSVR"]


@enforce_types
class AimodelSS(StrMixin):
    __STR_OBJDIR__ = ["d"]

    def __init__(self, d: dict):
        self.d = d  # yaml_dict["aimodel_ss"]

        # test inputs
        if self.approach not in APPROACHES:
            raise ValueError(self.approach)

    # --------------------------------
    # yaml properties
    @property
    def approach(self) -> str:
        return self.d["approach"]  # eg "LIN"
