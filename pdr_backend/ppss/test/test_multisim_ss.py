from enforce_typing import enforce_types

from pdr_backend.ppss.sim_ss import SimSS

@enforce_types
def test_multisim_ss_main(tmpdir):
    yaml_str = fast_test_yaml_str(tmpdir)
    ppss = PPSS(yaml_str=yaml_str, network="development")
    ss = ppss.multisim_ss
    
    assert ss.multisim_ss.approach == "simplesweep"
    assert isinstance(ss.sweep_params, list)
    assert ss.sweep_params
    assert ss.n_combos > 1

    # str
    assert "MultisimSS" in str(ss)

def test_multisim_ss_test_dict():
    sweep_params = FIXME
    d = multisim_ss_test_dict(sweep_params)
    assert d["approach"] == "simplesweep"
    assert d["sweep_params] == sweep_params

    ss = MultisimSS(d)
    assert ss.approach == "simplesweep"
    assert ss.sweep_params
