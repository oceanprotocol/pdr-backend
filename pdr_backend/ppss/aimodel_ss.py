from typing import Optional, Tuple

from enforce_typing import enforce_types

from pdr_backend.util.strutil import StrMixin

CLASSIF_APPROACH_OPTIONS = [
    "ClassifLinearLasso",
    "ClassifLinearLasso_Balanced",
    "ClassifLinearRidge",
    "ClassifLinearRidge_Balanced",
    "ClassifLinearElasticNet",
    "ClassifLinearElasticNet_Balanced",
    "ClassifLinearSVM",
    "ClassifConstant",
]
REGR_APPROACH_OPTIONS = [
    "RegrLinearLS",
    "RegrLinearLasso",
    "RegrLinearRidge",
    "RegrLinearElasticNet",
    "RegrGaussianProcess",
    "RegrConstant",
]
APPROACH_OPTIONS = CLASSIF_APPROACH_OPTIONS + REGR_APPROACH_OPTIONS

WEIGHT_RECENT_OPTIONS = ["10x_5x", "10000x", "None"]
BALANCE_CLASSES_OPTIONS = ["SMOTE", "RandomOverSampler", "None"]
CALIBRATE_PROBS_OPTIONS = [
    "CalibratedClassifierCV_Sigmoid",
    "CalibratedClassifierCV_Isotonic",
    "None",
]
CALIBRATE_REGR_OPTIONS = ["CurrentYval", "None"]


class AimodelSS(StrMixin):
    __STR_OBJDIR__ = ["d"]

    @enforce_types
    def __init__(self, d: dict):
        """d -- yaml_dict["aimodel_ss"]"""
        self.d = d

        # test inputs
        if self.approach not in APPROACH_OPTIONS:
            raise ValueError(self.approach)
        if self.weight_recent not in WEIGHT_RECENT_OPTIONS:
            raise ValueError(self.weight_recent)
        if self.balance_classes not in BALANCE_CLASSES_OPTIONS:
            raise ValueError(self.balance_classes)
        if self.calibrate_probs not in CALIBRATE_PROBS_OPTIONS:
            raise ValueError(self.calibrate_probs)
        if self.calibrate_regr not in CALIBRATE_REGR_OPTIONS:
            raise ValueError(self.calibrate_regr)

    # --------------------------------
    # yaml properties

    @property
    def approach(self) -> str:
        """eg 'ClassifLinearRidge'"""
        return self.d["approach"]

    @property
    def weight_recent(self) -> str:
        """eg '10x_5x'"""
        return self.d["weight_recent"]

    @property
    def balance_classes(self) -> str:
        """eg 'SMOTE'"""
        return self.d["balance_classes"]

    @property
    def train_every_n_epochs(self) -> int:
        """eg 1. Train every 5 epochs"""
        return int(self.d["train_every_n_epochs"])

    @property
    def calibrate_probs(self) -> str:
        """eg 'CalibratedClassifierCV_Sigmoid'"""
        return self.d["calibrate_probs"]

    def calibrate_probs_skmethod(self, N: int) -> str:
        """
        @description
          Return the value for 'method' argument in sklearn
          CalibratedClassiferCV().

        @arguments
          N -- number of samples
        """
        if N < 200:
            return "sigmoid"

        c = self.calibrate_probs
        if c == "CalibratedClassifierCV_Sigmoid":
            return "sigmoid"
        if c == "CalibratedClassifierCV_Isotonic":
            return "isotonic"
        raise ValueError(c)

    @property
    def calibrate_regr(self) -> str:
        """eg 'CurrentYval'"""
        return self.d["calibrate_regr"]

    # --------------------------------
    # derivative properties
    @property
    def do_regr(self) -> bool:
        return self.approach[:4] == "Regr"

    @property
    def weight_recent_n(self) -> Tuple[int, int]:
        """@return -- (n_repeat1, n_repeat2)"""
        if self.weight_recent == "None":
            return 0, 0
        if self.weight_recent == "10x_5x":
            return 10, 5
        if self.weight_recent == "10000x":
            return 10000, 0
        raise ValueError(self.weight_recent)


# =========================================================================
# utilities for testing


@enforce_types
def aimodel_ss_test_dict(
    approach: Optional[str] = None,
    weight_recent: Optional[str] = None,
    balance_classes: Optional[str] = None,
    calibrate_probs: Optional[str] = None,
    calibrate_regr: Optional[str] = None,
) -> dict:
    """Use this function's return dict 'd' to construct AimodelSS(d)"""
    d = {
        "approach": approach or "ClassifLinearRidge",
        "weight_recent": weight_recent or "10x_5x",
        "balance_classes": balance_classes or "SMOTE",
        "train_every_n_epochs": 1,
        "calibrate_probs": calibrate_probs or "CalibratedClassifierCV_Sigmoid",
        "calibrate_regr": calibrate_regr or "None",
    }
    return d
