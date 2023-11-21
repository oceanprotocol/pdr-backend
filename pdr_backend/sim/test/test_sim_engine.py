from enforce_typing import enforce_types

from pdr_backend.ppss.ppss import PPSS, fast_test_yaml_str
from pdr_backend.sim.sim_engine import SimEngine


@enforce_types
def test_SimEngine(tmpdir):
    yaml_str = fast_test_yaml_str(tmpdir)
    ppss = PPSS("barge-pytest", yaml_str=yaml_str)
    sim_engine = SimEngine(ppss)
    sim_engine.run()
