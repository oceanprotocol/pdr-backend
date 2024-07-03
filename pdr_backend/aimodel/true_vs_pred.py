from typing import List, Tuple

from enforce_typing import enforce_types

from sklearn.metrics import log_loss, precision_recall_fscore_support
from statsmodels.stats.proportion import proportion_confint

PERF_NAMES = ["acc_est", "acc_l", "acc_u", "f1", "precision", "recall", "loss"]


class TrueVsPred:
    """
    True vs pred vals for a single aimodel, or for a history of models,
    + the performances that derive from true vs pred value info
    """

    @enforce_types
    def __init__(self):
        # 'i' is iteration number i
        self.truevals: List[bool] = []  # [i] : true value
        self.predprobs: List[float] = []  # [i] : model's pred. prob.

    @enforce_types
    def update(self, trueval: bool, predprob: float):
        self.truevals.append(trueval)
        self.predprobs.append(predprob)

    @property
    def predvals(self) -> List[bool]:
        """@return [i] : model pred. value"""
        return [p > 0.5 for p in self.predprobs]

    @property
    def n_correct(self) -> int:
        return sum(tv == pv for tv, pv in zip(self.truevals, self.predvals))

    @property
    def n_trials(self) -> int:
        return len(self.truevals)

    @enforce_types
    def accuracy(self) -> Tuple[float, float, float]:
        n_correct, n_trials = self.n_correct, self.n_trials
        acc_est = n_correct / n_trials
        acc_l, acc_u = proportion_confint(count=n_correct, nobs=n_trials)
        return (acc_est, acc_l, acc_u)

    @enforce_types
    def precision_recall_f1(self) -> Tuple[float, float, float]:
        (precision, recall, f1, _) = precision_recall_fscore_support(
            self.truevals,
            self.predvals,
            average="binary",
            zero_division=0.0,
        )
        return (precision, recall, f1)

    @enforce_types
    def log_loss(self) -> float:
        if min(self.truevals) == max(self.truevals):
            return 3.0  # magic number
        return log_loss(self.truevals, self.predprobs)

    @enforce_types
    def perf_names(self) -> List[str]:
        return PERF_NAMES

    @enforce_types
    def perf_values(self) -> List[float]:
        perfs_list = (
            list(self.accuracy()) + list(self.precision_recall_f1()) + [self.log_loss()]
        )
        assert len(perfs_list) == len(PERF_NAMES)
        return perfs_list
