from enforce_typing import enforce_types


@enforce_types
class SimModelPrediction:
    def __init__(
        self,
        conf_thr: float,
        prob_up_UP: float,
        prob_up_DOWN: float,
    ):
        # ppss.trader_ss.sim_confidence_threshold
        self.conf_thr = conf_thr

        # core attributes
        self.prob_up_UP = prob_up_UP
        self.prob_up_DOWN = prob_up_DOWN

        # derived attributes
        self.prob_down_DOWN = 1.0 - self.prob_up_DOWN
        
        if self.models_in_conflict():
            self.conf_up = 0.0
            self.conf_down = 0.0
            self.pred_up = False
            self.pred_down = False
            self.prob_up_MERGED = 0.5
            
        elif self.prob_up_UP >= self.prob_down_DOWN:
            self.conf_up = (prob_up_UP - 0.5) * 2.0  # to range [0,1]
            self.conf_down = 0.0
            self.pred_up = self.conf_up > self.conf_thr
            self.pred_down = False
            self.prob_up_MERGED = self.prob_up_UP
            
        else: # prob_down_DOWN > prob_up_UP
            self.conf_up = 0.0
            self.conf_down = (self.prob_down_DOWN - 0.5) * 2.0
            self.pred_up = False
            self.pred_down = self.conf_down > self.conf_thr
            self.prob_up_MERGED = 1.0 - self.prob_down_DOWN
    
    @enforce_types
    def do_trust_models(self) -> bool:
        return _do_trust_models(
            self.pred_up, self.pred_down, self.prob_up_UP, self.prob_down_DOWN,
        )

    @enforce_types
    def models_in_conflict(self) -> bool:
        return _models_in_conflict(self.prob_up_UP, self.prob_down_DOWN)


@enforce_types
def _do_trust_models(
    pred_up:bool,
    pred_down:bool,
    prob_up_UP:float,
    prob_down_DOWN:float,
) -> bool:
    """Do we trust the models enough to take prediction / trading action?"""
    # preconditions
    if pred_up and pred_down:
        raise ValueError("can't have pred_up=True and pred_down=True")
    if pred_up and prob_down_DOWN > prob_up_UP:
        raise ValueError("can't have pred_up=True with prob_DOWN dominant")
    if pred_down and prob_up_UP > prob_down_DOWN:
        raise ValueError("can't have pred_down=True with prob_UP dominant")
    if not (0.0 <= prob_up_UP <= 1.0):
        raise ValueError(prob_up_UP)
    if not (0.0 <= prob_down_DOWN <= 1.0):
        raise ValueError(prob_down_DOWN)

    # main test
    return (pred_up or pred_down) \
        and not _models_in_conflict(prob_up_UP, prob_down_DOWN)

@enforce_types
def _models_in_conflict(prob_up_UP: float, prob_down_DOWN: float) -> bool:
    """Does the UP model conflict with the DOWN model?"""
    # preconditions
    if not (0.0 <= prob_up_UP <= 1.0):
        raise ValueError(prob_up_UP)
    if not (0.0 <= prob_down_DOWN <= 1.0):
        raise ValueError(prob_down_DOWN)

    # main test
    return (prob_up_UP > 0.5 and prob_down_DOWN > 0.5) or \
        (prob_up_UP < 0.5 and prob_down_DOWN < 0.5)
