from enforce_typing import enforce_types
import numpy as np
from numpy.testing import assert_array_equal

from pdr_backend.sim.constants import Dirn, UP, DOWN
from pdr_backend.sim.sim_model_data import SimModelData, SimModelData1Dir

@enforce_types
def test_sim_model_data_1dir():
    # build data
    X_UP = np.array([[1.,2.,3.,4.],[5.,6.,7.,8.]]) # 4 x 2
    ytrue_UP = np.array([True, True, False, True]) # 4
    
    # basic tests
    assert_array_equal(X_UP, data_UP.X)
    assert_array_equal(ytrue_UP, data_UP.ytrue)

    # test properties
    assert data_UP.st == 0
    assert data_UP.fin == (4 - 1) == 3
    assert_array_equal(data_UP.X_train, X_UP[0:3,:])
    assert_array_equal(data_UP.X_test, X_UP[3:3+1,:])
    assert_array_equal(data_UP.ytrue_train, ytrue_train[0:3])
                       
@enforce_types
def test_sim_model_data_both_dirs():
    # build data
    X_UP = np.array([[1.,2.,3.,4.],[5.,6.,7.,8.]])
    ytrue_UP = np.array([True, True, False, True])
    
    X_DOWN = np.array([[11.,12.,13.,14.],[15.,16.,17.,18.]])
    ytrue_DOWN = np.array([False, True, False, True])

    data_UP = SimModelData1Dir(X_UP, ytrue_UP)
    data_DOWN = SimModelData1Dir(X_DOWN, ytrue_DOWN)
    data = SimModelData(data_UP, data_DOWN)

    # basic tests
    assert sorted(data.keys()) == sorted([UP, DOWN])
    for key in data:
        assert isinstance(key, Dirn)
    assert isinstance(data[UP], SimModelData1Dir)
    assert isinstance(data[DOWN], SimModelData1Dir)
    
    assert_array_equal(X_UP, data[UP].X)
    assert_array_equal(ytrue_UP, data[UP].ytrue)
    
    assert_array_equal(X_DOWN, data[DOWN].X)
    assert_array_equal(ytrue_DOWN, data[DOWN].ytrue)

    
