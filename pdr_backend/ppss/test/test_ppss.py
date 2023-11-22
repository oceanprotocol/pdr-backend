import os

from enforce_typing import enforce_types
import pytest

from pdr_backend.ppss.ppss import PPSS, fast_test_yaml_str


@enforce_types
def test_bad_network_name(tmpdir):
    yaml_str = fast_test_yaml_str(tmpdir)
    with pytest.raises(ValueError):
        PPSS(yaml_str=yaml_str, network="foo network")

        
@enforce_types
def test_ppss_from_file(tmpdir):
    yaml_str = fast_test_yaml_str(tmpdir)
    yaml_filename = os.path.join(tmpdir, "ppss.yaml")
    with open(yaml_filename, "a") as f:
        f.write(yaml_str)

    _test_ppss(yaml_filename=yaml_filename, network="development")


@enforce_types
def test_ppss_from_str(tmpdir):
    yaml_str = fast_test_yaml_str(tmpdir)
    _test_ppss(yaml_str=yaml_str, network="development")


@enforce_types
def test_ppss_default_network(tmpdir):
    yaml_str = fast_test_yaml_str(tmpdir)
    _test_ppss(yaml_str=yaml_str, network=None)


@enforce_types
def _test_ppss(yaml_filename=None, yaml_str=None, network=None):
    # construct
    ppss = PPSS(yaml_filename, yaml_str, network)

    # test network
    if network is None:
        assert isinstance(ppss.web3_pp.network, str)
    else:
        assert ppss.web3_pp.network == network

    # yaml properties - test lightly, since each *_pp and *_ss has its tests
    #  - so just do one test for each of this class's pp/ss attribute
    assert ppss.data_pp.timeframe in ["5m", "1h"]
    assert isinstance(ppss.data_ss.st_timestr, str)
    assert ppss.dfbuyer_ss.weekly_spending_limit >= 0
    assert ppss.model_ss.approach == "LIN"
    assert ppss.payout_ss.batch_size >= 0
    assert 1 <= ppss.predictoor_ss.s_until_epoch_end <= 120
    assert isinstance(ppss.sim_ss.do_plot, bool)
    assert 0.0 <= ppss.trader_pp.fee_percent <= 0.99
    assert "USD" in ppss.trader_ss.buy_amt_str
    assert ppss.trueval_ss.batch_size >= 0
    assert isinstance(ppss.web3_pp.address_file, str)

    # str
    s = str(ppss)
    assert "data_pp" in s
    assert "data_ss" in s
    assert "dfbuyer_ss" in s
    assert "model_ss" in s
    assert "payout_ss" in s
    assert "predictoor_ss" in s
    assert "sim_ss" in s
    assert "trader_pp" in s
    assert "trader_ss" in s
    assert "trueval_ss" in s
    assert "web3_pp" in s
