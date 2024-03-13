import csv
import logging
import os
from typing import List, Union

from enforce_typing import enforce_types

from pdr_backend.ppss.ppss import PPSS
from pdr_backend.sim.sim_engine import SimEngine
from pdr_backend.sim.sim_state import SimState
from pdr_backend.util.time_types import UnixTimeMs

logger = logging.getLogger("multisim_engine")

class MultisimEngine:
    @enforce_types
    def __init__(self, ppss: PPSS):
        self.ppss = ppss

    def run(self):
        logger.info("Multisim engine: start")
        self.initialize_csv()
        n_combos = self.ppss.multisim_ss.n_combos
        for i in range(n_combos):
            logger.info("Multisim run #%s/%s: start" % (i+1, n_combos))
            if self.ppss.sim_ss.do_plot:
                raise ValueError("For multisim, must have sim_ss.do_plot=False")
            raise "FIXME update PPSS for sim engine now"
            ppss = self.ppss
            sim_engine = SimEngine(ppss)
            sim_engine.run()
            run_metrics = sim_engine.st.recent_metrics()
            self.update_csv(run_metrics)
            logger.info("Multisim run #%s/%s: done" % (i+1, self.n_engines))
            
        logger.info("Multisim engine: done. Output file: %s" % self.csv_file)
        
    @enforce_types
    def initialize_csv(self):
        filebase = f"multisim_metrics_{UnixTimeMs.now()}.csv"
        self.csv_file = os.path.join(self.ppss.sim_ss.log_dir, filebase)
        assert not os.path.exists(self.csv_file), self.csv_file
        with open(self.csv_file, "w") as f:
            writer = csv.writer(f)
            row = SimState.recent_metrics_names()
            writer.writerow(row)
        logger.info("Multisim output file: %s" % self.csv_file)
        
    @enforce_types
    def update_csv(self, run_metrics: List[Union[int,float]]):
        """
        @description
          Update csv with metrics from a given sim run

        @arguments
          run_metrics -- output of SimState.recent_metrics()
        """
        assert os.path.exists(self.csv_file), csv_dir
        with open(self.csv_file, "w") as f:
            writer = csv.writer(f)
            row = run_metrics
            writer.writerow(row)

