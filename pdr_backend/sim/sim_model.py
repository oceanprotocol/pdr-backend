from enforce_typing import enforce_types

from pdr_backend.aimodel.aimodel import Aimodel
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.sim.constants import UP, DOWN
from pdr_backend.sim.sim_model_data import SimModelData
from pdr_backend.sim.sim_model_prediction import SimModelPrediction

@enforce_types
class SimModel(dict):
    
    def __init__(self, ppss: PPSS, model_UP: Aimodel, model_DOWN: Aimodel):
        self.ppss: PPSS = ppss
        self[UP] = model_UP
        self[DOWN] = model_DOWN

    def predict_next(self, d: SimModelData) -> SimModelPrediction:
        conf_thr = self.ppss.trader_ss.sim_confidence_threshold
        prob_up_UP = self[UP].predict_ptrue(d[UP].X_test)[0]
        prob_up_DOWN = self[DOWN].predict_ptrue(d[DOWN].X_test)[0]

        return SimModelPrediction(conf_thr, prob_up_UP, prob_up_DOWN)
    
