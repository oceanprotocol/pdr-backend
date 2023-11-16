import os

from pdr_backend.data_eng.constants import DEFAULT_PPSS_YAML_FILENAME
from pdr_backend.data_eng.ppss import PPSS
from pdr_backend.sim.sim_engine import SimEngine

def run():
    ppss = PPSS(yaml_filename)

    print(ppss)

    sim_engine = SimEngine(ppss)

    sim_engine.run()
