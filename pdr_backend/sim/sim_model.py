from enforce_typing import enforce_types

from pdr_backend.aimodel.aimodel import Aimodel
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.sim.constants import UP, DOWN
from pdr_backend.sim.sim_model_data import SimModelData
from pdr_backend.sim.sim_model_prediction import SimModelPrediction

@enforce_types
class SimModel(dict):
    
    def __init__(self, model_UP: Aimodel, model_DOWN: Aimodel):
        self[UP] = model_UP
        self[DOWN] = model_DOWN
        
    def predict_next(self, d: SimModelData) -> dict:
        predprob_UP = self[UP].predict_ptrue(d[UP].X_test)[0]
        predprob_DOWN = self[DOWN].predict_ptrue(d[DOWN].X_test)[0]
        return {UP: predprob_UP, DOWN: predprob_DOWN}
    
