from enforce_typing import enforce_types

from pdr_backend.cli.predict_train_feedsets import PredictTrainFeedset
from pdr_backend.ppss.aimodel_data_ss import AimodelDataSS
from pdr_backend.ppss.ppss import mock_feed_ppss
from pdr_backend.ppss.predictoor_ss import PredictoorSS
from pdr_backend.sim.sim_model_data_factory import SimModelDataFactory


@enforce_types
def test_sim_model_data_factory__basic(tmpdir):
    #base data
    data_f = _factory(tmpdir)

    # attributes
    assert isinstance(data_f.ppss, PPSS)
    assert isinstance(data_f.predict_train_feedset, PredictTrainFeedset)
                          
    # properties
    assert isinstance(data_f.pdr_ss, PredictoorSS)
    assert isinstance(data_f.aimodel_data_ss, AimodelDataSS)
    assert 0.0 < data_f.class_thr < 1.0
    assert isinstance(data_f.aimodel_data_factory, AimodelDataFactory)

@enforce_types
def test_sim_model_data_factory__testshift(tmpdir):
    #base data
    data_f = _factory(tmpdir)
    test_i = 3
    
    # do work
    test_n = data_f.ppss.sim_ss.test_n

    # test
    assert data_f.testshift(test_i) == test_n - test_i - 1
    
@enforce_types
def test_sim_model_data_factory__thr_UP__thr_DOWN(tmpdir):
    #base data
    data_f = _factory(tmpdir)
    cur_close = 8.0
    class_thr = data_f.ppss.predictoor_ss.aimodel_ss.class_thr
    
    # do work
    thr_UP = data_f.thr_UP(cur_close)
    thr_DOWN = data_f.thr_DOWN(cur_close)

    # test
    assert class_thr > 0.0
    assert thr_DOWN < cur_close < thr_UP
    assert thr_UP == cur_close * (1 + class_thr)
    assert thr_DOWN == cur_close * (1 - class_thr)

@enforce_types
def test_sim_model_data_factory_build(tmpdir):
    #base data
    data_f = _factory(tmpdir)
    test_i = 3
    
    # do work
    data = data_f.build(test_i, mergedohlcv_df)

    # test
    # - keep this light for now. Maybe expand when things stabilize
    assert isinstance(data, SimModelData)
    assert 9.0 < np.min(data[UP].X) < np.max(data[UP].X) < 9.8 # all 'high'
    assert 0.0 < np.min(data[DOWN].X) < np.max(data[DOWN].X) < 0.8 # all 'low'

    
@enforce_types
def _factory(tmpdir) -> SimModelDataFactory:
    feed, ppss = mock_feed_ppss("5m", "binance", "BTC/USDT")
    predict_train_feedset = PredictTrainFeedset(predict=feed, train_on=[feed])
    data_f = SimModelDataFactory(ppss, predict_train_feedset)
    return data_f

@enforce_types
def _merged_ohlcv_df() -> pl.DataFrame:
    return pl.DataFrame(
        {
            # - every column in df is ordered from youngest to oldest
            # - high values are 9.x, 9.y, ..; low are 0.x, 0.y, ..; close is b/w
            "timestamp": [1, 2, 3, 4, 5, 6, 7],
            "binanceus:ETH/USDT:high":  [9.1, 9.6, 9.8, 9.4, 9.2, 9.5, 9.7],
            "binanceus:ETH/USDT:low" :  [0.1, 0.6, 0.8, 0.4, 0.2, 0.5, 0.7],
            "binanceus:ETH/USDT:close": [2.1, 3.6, 4.6, 5.6, 6.2, 7.5, 8.7],
        }
