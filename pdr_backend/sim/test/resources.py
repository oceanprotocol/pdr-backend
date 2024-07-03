from enforce_typing import enforce_types
import numpy as np

from pdr_backend.sim.sim_model_data import SimModelData, SimModelData1Dir


@enforce_types
def get_Xy_UP() -> tuple:
    X_UP = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0], [7.0, 8.0]])  # 4 x 2
    ytrue_UP = np.array([True, True, False, True])  # 4
    return (X_UP, ytrue_UP)


@enforce_types
def get_Xy_DOWN() -> tuple:
    X_DOWN = np.array([[11.0, 12.0], [13.0, 14.0], [15.0, 16.0], [17.0, 18.0]])
    ytrue_DOWN = np.array([False, True, False, True])
    return (X_DOWN, ytrue_DOWN)


@enforce_types
def get_sim_model_data() -> SimModelData:
    (X_UP, ytrue_UP) = get_Xy_UP()
    (X_DOWN, ytrue_DOWN) = get_Xy_DOWN()

    colnames_UP = ["x0_high", "x1_high"]
    colnames_DOWN = ["x0_low", "x1_low"]

    data_UP = SimModelData1Dir(X_UP, ytrue_UP, colnames_UP)
    data_DOWN = SimModelData1Dir(X_DOWN, ytrue_DOWN, colnames_DOWN)
    data = SimModelData(data_UP, data_DOWN)

    return data
