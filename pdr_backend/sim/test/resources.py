import numpy as np

from pdr_backend.sim.sim_model_data import SimModelData, SimModelData1Dir

@enforce_types
def get_sim_model_data() -> SimModelData:
    X_UP = np.array([[1.,2.,3.,4.],[5.,6.,7.,8.]])
    ytrue_UP = np.array([True, True, False, True])
    
    X_DOWN = np.array([[11.,12.,13.,14.],[15.,16.,17.,18.]])
    ytrue_DOWN = np.array([False, True, False, True])

    data_UP = SimModelData1Dir(X_UP, ytrue_UP)
    data_DOWN = SimModelData1Dir(X_DOWN, ytrue_DOWN)
    data = SimModelData(data_UP, data_DOWN)

    return data
