from enforce_typing import enforce_types


# pylint: disable=too-many-instance-attributes
@enforce_types
class GrpmodelPrediction:
    def __init__(
        self,
        conf_thr: float,
        # UP model's probability that next high will go > prev close+%
        prob_UP: float,
        # DOWN model's probability that next low will go < prev close-%
        prob_DOWN: float,
    ):
        # ensure not np.float64. Why: applying ">" gives np.bool --> problems
        prob_UP, prob_DOWN = float(prob_UP), float(prob_DOWN)

        # ppss.trader_ss.sim_confidence_threshold
        self.conf_thr = conf_thr

        # core attributes
        self.prob_UP = prob_UP
        self.prob_DOWN = prob_DOWN

        # derived attributes
        if self.models_in_conflict():
            self.conf_up = 0.0
            self.conf_down = 0.0
            self.pred_up = False
            self.pred_down = False
            self.prob_up_MERGED = 0.5

        elif self.prob_UP >= self.prob_DOWN:
            self.conf_up = (prob_UP - 0.5) * 2.0  # to range [0,1]
            self.conf_down = 0.0
            self.pred_up = self.conf_up > self.conf_thr
            self.pred_down = False
            self.prob_up_MERGED = self.prob_UP

        else:  # prob_DOWN > prob_UP
            self.conf_up = 0.0
            self.conf_down = (self.prob_DOWN - 0.5) * 2.0
            self.pred_up = False
            self.pred_down = self.conf_down > self.conf_thr
            self.prob_up_MERGED = 1.0 - self.prob_DOWN

    def do_trust_models(self) -> bool:
        do_trust = _do_trust_models(
            self.pred_up,
            self.pred_down,
            self.prob_UP,
            self.prob_DOWN,
        )
        return do_trust

    def models_in_conflict(self) -> bool:
        return _models_in_conflict(self.prob_UP, self.prob_DOWN)


@enforce_types
def _do_trust_models(
    pred_up: bool,
    pred_down: bool,
    prob_UP: float,
    prob_DOWN: float,
) -> bool:
    """Do we trust the models enough to take prediction / trading action?"""
    # preconditions
    if not 0.0 <= prob_UP <= 1.0:
        raise ValueError(prob_UP)
    if not 0.0 <= prob_DOWN <= 1.0:
        raise ValueError(prob_DOWN)
    if pred_up and pred_down:
        raise ValueError("can't have pred_up=True and pred_down=True")
    if pred_up and prob_DOWN > prob_UP:
        raise ValueError("can't have pred_up=True with prob_DOWN dominant")
    if pred_down and prob_UP > prob_DOWN:
        raise ValueError("can't have pred_down=True with prob_UP dominant")

    # main test
    return (pred_up or pred_down) and not _models_in_conflict(prob_UP, prob_DOWN)


@enforce_types
def _models_in_conflict(prob_UP: float, prob_DOWN: float) -> bool:
    """Does the UP model conflict with the DOWN model?"""
    # preconditions
    if not 0.0 <= prob_UP <= 1.0:
        raise ValueError(prob_UP)
    if not 0.0 <= prob_DOWN <= 1.0:
        raise ValueError(prob_DOWN)

    # main test
    return (prob_UP > 0.5 and prob_DOWN > 0.5) or (prob_UP < 0.5 and prob_DOWN < 0.5)
