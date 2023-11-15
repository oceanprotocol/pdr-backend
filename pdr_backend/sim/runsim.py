#!/usr/bin/env python
import os

from pdr_backend.data_eng.constants import DEFAULT_PPSS_YAML_FILENAME
from pdr_backend.data_eng.ppss import PPSS
from pdr_backend.sim.trade_engine import TradeEngine

yaml_filename = os.path.abspath(DEFAULT_PPSS_YAML_FILENAME)
ppss = PPSS(yaml_filename)

print(ppss)

trade_engine = TradeEngine(ppss)

trade_engine.run()


