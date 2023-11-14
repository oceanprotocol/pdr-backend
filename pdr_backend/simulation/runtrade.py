#!/usr/bin/env python
import os

from pdr_backend.data_eng.ppss import PPSS
from pdr_backend.simulation.trade_engine import TradeEngine

yaml_filename = os.path.abspath("ppss.yaml")
ppss = PPSS(yaml_filename)

print(ppss)

trade_engine = TradeEngine(ppss)

trade_engine.run()


