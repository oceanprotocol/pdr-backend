import copy
import csv
import logging
import os
from typing import List, Union

from enforce_typing import enforce_types
import pandas as pd

from pdr_backend.cli.nested_arg_parser import flat_to_nested_args
from pdr_backend.ppss.multisim_ss import MultisimSS
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.sim.sim_engine import SimEngine
from pdr_backend.sim.sim_state import SimState
from pdr_backend.util.dictutil import recursive_update
from pdr_backend.util.time_types import UnixTimeMs

logger = logging.getLogger("multisim_engine")


class MultisimEngine:
    @enforce_types
    def __init__(self, d: dict):
        """
        @arguments
          d -- created via PPSS.constructor_dict()
        """
        self.d: dict = d
        self.network = "development"
        
        filebase = f"multisim_metrics_{UnixTimeMs.now()}.csv"
        self.csv_file = os.path.join(self.ppss.sim_ss.log_dir, filebase)

    @property
    def ppss(self) -> PPSS:
        return PPSS(d=self.d, network=self.network)
    
    @property
    def ss(self) -> MultisimSS:
        return self.ppss.multisim_ss

    @enforce_types
    def run(self):
        ss = self.ss
        logger.info("Multisim engine: start")
        self.initialize_csv()
        n_points = ss.n_points
        for i in range(n_points):
            logger.info("Multisim run #%s/%s: start" % (i + 1, ss.n_points))
            ppss = self.ppss_i(i)
            sim_engine = SimEngine(ppss)
            sim_engine.run()
            run_metrics = sim_engine.st.recent_metrics()
            self.update_csv(run_metrics)
            logger.info("Multisim run #%s/%s: done" % (i + 1, ss.n_points))

        logger.info("Multisim engine: done. Output file: %s" % self.csv_file)

    def ppss_i(self, i: int) -> PPSS:
        """PPSS for sim_engine run #i"""
        point_i = self.ss.point_i(i)
        nested_args = flat_to_nested_args(point_i)
        d = copy.deepcopy(self.d)
        recursive_update(d, nested_args)
        ppss = PPSS(d=d, network=self.network)
        assert not ppss.sim_ss.do_plot, "don't plot for multisim_engine"
        return ppss
    
    @enforce_types
    def initialize_csv(self):
        assert not os.path.exists(self.csv_file), self.csv_file
        spaces: List[int] = _spaces()
        with open(self.csv_file, "w") as f:
            writer = csv.writer(f)
            row = self.csv_header()
            writer.writerow(
                [name.rjust(space) for name, space in zip(row, spaces)]
            )
        logger.info("Multisim output file: %s" % self.csv_file)

    @enforce_types
    def csv_header(self) -> List[str]:
        header = []
        header += SimState.recent_metrics_names()
        return header

    @enforce_types
    def update_csv(self, run_metrics: List[Union[int, float]]):
        """
        @description
          Update csv with metrics from a given sim run

        @arguments
          run_metrics -- output of SimState.recent_metrics()
        """
        assert os.path.exists(self.csv_file), csv_dir
        spaces: List[int] = _spaces()
        with open(self.csv_file, "a") as f:
            writer = csv.writer(f)
            row = run_metrics
            assert len(row) == len(self.csv_header())
            writer.writerow(
                [(f"{val:.4f}").rjust(space) for val, space in zip(row, spaces)]
            )

    @enforce_types
    def load_csv(self) -> pd.DataFrame:
        """Load csv as a pandas Dataframe."""
        df = pd.read_csv(self.csv_file)
        df.rename(columns=lambda x: x.strip(), inplace=True) # strip whitespace
        return df

    
@enforce_types
def _spaces() -> List[int]:
    """How much space for each particular column, in the csv file?"""
    return [max(len(name), 6) + 2 for name in SimState.recent_metrics_names()]
    

