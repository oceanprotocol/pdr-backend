import csv
import logging
import os

from enforce_typing import enforce_types

from pdr_backend.sim.sim_engine import SimEngine

logger = logging.getLogger("multisim")

class Multisim:
    @enforce_types
    def __init__(self, ppss: PPSS, n_runs:int):
        if ppss.sim_ss.do_plot:
            raise ValueError("For multisim, must have sim_ss.do_plot=False")
        self.engines = [SimEngine(ppss) for i in range(n_runs)]
        

    def run(self):
        logger.info("Multisim: start")
        self.initalize_csv()
        for i, engine in zip(engines):
            logger.info("Multisim run #%s/%s: start" % (i+1, len(self.engines)))
            FIXME update engine PPSS
            engine.run()
            run_metrics = engine.st.recent_metrics()
            self.update_csv(run_metrics)
            logger.info("Multisim run #%s/%s: done" % (i+1, len(self.engines)))
            
        logger.info("Multisim: done all. Output file: %s" % self.csv_file)
        
    @enforce_types
    def initialize_csv(self):
        filebase = f"multisim_metrics_{UnixTimeMs.now()}.csv"
        self.csv_file = os.path.join(self.ppss.sim_ss.log_dir, filebase)
        assert not os.path.exists(csv_file), csv_file
        with open(self.csv_file, "w") as f:
            writer = csv.writer(f)
            row = engine.st.recent_metrics_names()
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

