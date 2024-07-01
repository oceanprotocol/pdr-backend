from typing import Optional

from enforce_typing import enforce_types

from pdr_backend.aimodel.aimodel_factory import AimodelFactory
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.sim.constants import UP, DOWN
from pdr_backend.sim.sim_model import SimModel
from pdr_backend.sim.sim_model_data import SimModelData

class SimModelFactory:    
    @enforce_types
    def __init__(self, ppss: PPSS):
        self.ppss = ppss

    @property
    def aimodel_ss(self):
        return self.ppss.predictoor_ss.aimodel_ss
      
    @enforce_types
    def do_build(self, prev_model: Optional[SimModel], test_i: int) -> bool:
        """Update/train model?"""
        n = self.aimodel_ss.train_every_n_epochs
        return prev_model is None or test_i % n == 0
      
    @enforce_types
    def build(self, data: SimModelData) -> SimModel:
        model_f = AimodelFactory(self.aimodel_ss)
        
        model_UP = model_f.build(
            data[UP].X_train,
            data[UP].ytrue_train,
            None,
            None,
        )
        
        model_DOWN = model_f.build(
            data[DOWN].X_train,
            data[DOWN].ytrue_train,
            None,
            None,
        )
        
        sim_model = SimModel(self.ppss, model_UP, model_DOWN)
        return sim_model
