from enforce_typing import enforce_types


@enforce_types
class ModelSS:
    def __init__(
        self,
        model_approach: str,  # PREV,LIN,GPR,SVR,NuSVR,LinearSVR
    ):
        self.model_approach = model_approach
        self.var_with_prev = None

    def __str__(self) -> str:
        s = "ModelSS={\n"
        s += f"  model_approach={self.model_approach}\n"
        s += f"  var_with_prev={self.var_with_prev}\n"
        s += "/ModelSS}\n"
        return s
