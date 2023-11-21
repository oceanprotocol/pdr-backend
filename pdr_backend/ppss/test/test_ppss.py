import os
from enforce_typing import enforce_types

from pdr_backend.ppss.ppss import PPSS, fast_test_yaml_str

@enforce_types
def test_ppss_from_file(tmpdir):
    yaml_str = fast_test_yaml_str(tmpdir)
    yaml_filename = os.path.join(tmpdir, "ppss.yaml")
    f = open(yaml_filename, "a")
    f.write(yaml_str)
    f.close()

    _test_ppss(yaml_filename=yaml_filename)


@enforce_types
def test_ppss_from_str(tmpdir):
    yaml_str = fast_test_yaml_str(tmpdir)
    _test_ppss(yaml_str=yaml_str)


@enforce_types
def _test_ppss(yaml_filename=None, yaml_str=None):
    # construct
    ppss = PPSS("sapphire-testnet", yaml_filename, yaml_str)

    # yaml properties - test lightly, since each *_pp and *_ss has its tests
    assert ppss.data_pp.timeframe in ["5m", "1h"]
    assert isinstance(ppss.data_ss.st_timestr, str)
    assert ppss.model_ss.approach == "LIN"
    assert 1 <= ppss.predictoor_ss.s_until_epoch_end <= 120
    assert 0.0 <= ppss.trader_pp.fee_percent <= 0.99
    assert "USD" in ppss.trader_ss.buy_amt_str
    assert isinstance(ppss.sim_ss.do_plot, bool)

    # str
    s = str(ppss)
    assert "data_pp" in s
    assert "data_ss" in s
    assert "model_ss" in s
    assert "predictoor_ss" in s
    assert "trader_pp" in s
    assert "trader_ss" in s
    assert "sim_ss" in s


@enforce_types
def _test_bad_network_name():
    yaml_str = fast_test_yaml_str(tmpdir)
    with pytest.raises(ValueError):
        ppss = PPSS(network="foo network", yaml_str=yaml_str)
    
