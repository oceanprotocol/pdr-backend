from enforce_typing import enforce_types

from pdr_backend.simulation.sim_ss import SimSS


@enforce_types
def test_sim_ss(tmpdir):
    ss = SimSS(
        do_plot=False,
        logpath=str(tmpdir),
    )
    assert not ss.do_plot
    assert ss.logpath == str(tmpdir)
    assert "SimSS" in str(ss)
