from unittest.mock import Mock

from enforce_typing import enforce_types
import numpy as np

from pdr_backend.aimodel.aimodel import Aimodel
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.sim.sim_model import SimModel
from pdr_backend.sim.sim_model_data import SimModelData, SimModelData1Dir
from pdr_backend.sim.sim_model_prediction import SimModelPrediction

@enforce_types
def test_sim_model():
    ppss = Mock(spec=PPSS)
    ppss.trader_ss = Mock()
    ppss.trader_ss.sim_confidence_threshold = 0.1
    
    model_UP = Mock(spec=Aimodel)
    model_UP.predict_ptrue = Mock(return_value=np.array([0.1, 0.2, 0.3]))
    model_DOWN = Mock(spec=Aimodel)
    model_DOWN.predict_ptrue = Mock(return_value=np.array([0.7, 0.8, 0.9]))
    model = SimModel(ppss, model_UP, model_DOWN)

    data_UP = Mock(spec=SimModelData1Dir)
    data_DOWN = Mock(spec=SimModelData1Dir)
    d = SimModelData(data_UP, data_DOWN)
    p = model.predict_next(d)
    assert isinstance(p, SimModelPrediction)
    
