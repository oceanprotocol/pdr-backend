#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import asyncio
import copy
import csv
import logging
import os
import uuid
from typing import List, Union

import numpy as np
import pandas as pd
from enforce_typing import enforce_types

from pdr_backend.cli.nested_arg_parser import flat_to_nested_args
from pdr_backend.ppss.multisim_ss import MultisimSS
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.sim.sim_engine import SimEngine
from pdr_backend.sim.sim_state import SimState
from pdr_backend.util.dictutil import recursive_update
from pdr_backend.util.point import Point
from pdr_backend.util.time_types import UnixTimeMs

logger = logging.getLogger("multisim_engine")
lock = asyncio.Lock()


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
        log_dir = self.ppss.sim_ss.log_dir  # type: ignore[attr-defined]
        self.csv_file = os.path.join(log_dir, filebase)

    @property
    def ppss(self) -> PPSS:
        return PPSS(d=self.d, network=self.network)

    @property
    def ss(self) -> MultisimSS:
        return self.ppss.multisim_ss  # type: ignore

    @enforce_types
    def run(self):
        ss = self.ss
        logger.info("Multisim engine: start. # runs = %s", ss.n_runs)
        self.initialize_csv_with_header()
        asyncio.run(self.run_async(ss.n_runs))

    @enforce_types
    async def run_async(self, n_runs):
        tasks = []

        for run_i in range(n_runs):
            tasks.append(self.run_one(run_i))

        await asyncio.gather(*tasks)

    @enforce_types
    async def run_one(self, run_i: int):
        point_i = self.ss.point_i(run_i)
        logger.info("Multisim run_i=%s: start. Vals=%s", run_i, point_i)
        ppss = self.ppss_from_point(point_i)
        feedset = ppss.predictoor_ss.predict_train_feedsets[0]
        multi_id = str(uuid.uuid4())
        sim_engine = SimEngine(ppss, feedset, multi_id)
        sim_engine.disable_realtime_state()
        sim_engine.run()
        st = sim_engine.st
        recent_metrics = st.recent_metrics()

        # below, the "[1:]" is to avoid the first sample, which may be off
        run_metrics = {
            "acc_est": recent_metrics["acc_est"],
            "acc_l": recent_metrics["acc_l"],
            "acc_u": recent_metrics["acc_u"],
            "f1": np.mean(st.aim.f1s),
            "precision": np.mean(st.aim.precisions[1:]),
            "recall": np.mean(st.aim.recalls[1:]),
            "loss": np.mean(st.aim.losses[1:]),
            "yerr": np.mean(st.aim.yerrs[1:]),
            "pdr_profit_OCEAN": np.sum(st.pdr_profits_OCEAN),
            "trader_profit_USD": np.sum(st.trader_profits_USD),
        }
        run_metrics_list = list(run_metrics.values())
        async with lock:
            self.update_csv(run_i, run_metrics_list, point_i)
            logger.info("Multisim run_i=%s: done", run_i)

        logger.info("Multisim engine: done. Output file: %s", self.csv_file)

    def ppss_from_point(self, point_i: Point) -> PPSS:
        """
        @description
          Compute PPSS for sim_engine run #i

        @arguments
          point_i -- value of each sweep param
        """
        nested_args = flat_to_nested_args(point_i)
        d = copy.deepcopy(self.d)
        recursive_update(d, nested_args)
        ppss = PPSS(d=d, network=self.network)
        return ppss

    @enforce_types
    def csv_header(self) -> List[str]:
        # put metrics first, because point_meta names/values can be superlong
        header = []
        header += ["run_number"]
        header += SimState.recent_metrics_names()
        header += list(self.ss.point_meta.keys())
        return header

    @enforce_types
    def spaces(self) -> List[int]:
        buf = 3
        spaces = []
        spaces += [len("run_number") + buf]
        spaces += [max(len(name), 6) + buf for name in SimState.recent_metrics_names()]

        for var, cand_vals in self.ss.point_meta.items():
            var_len = len(var)
            max_val_len = max(len(str(cand_val)) for cand_val in cand_vals)
            space = max(var_len, max_val_len) + buf
            spaces.append(space)

        return spaces

    @enforce_types
    def initialize_csv_with_header(self):
        assert not os.path.exists(self.csv_file), self.csv_file
        spaces = self.spaces()
        with open(self.csv_file, "w") as f:
            writer = csv.writer(f)
            row = self.csv_header()
            writer.writerow([name.rjust(space) for name, space in zip(row, spaces)])
        logger.info("Multisim output file: %s", self.csv_file)

    @enforce_types
    def update_csv(
        self,
        run_i: int,
        run_metrics: List[Union[int, float]],
        point_i: Point,
    ):
        """
        @description
          Update csv with metrics from a given sim run

        @arguments
          run_i - it's run #i
          run_metrics -- output of SimState.recent_metrics() for run #i
          point_i -- value of each sweep param, for run #i
        """
        assert os.path.exists(self.csv_file), self.csv_file
        spaces = self.spaces()

        def _val2str(val):
            if isinstance(val, (float, int)):
                return f"{val:.4f}"
            return str(val)

        with open(self.csv_file, "a") as f:
            writer = csv.writer(f)
            row = [str(run_i)] + run_metrics + list(point_i.values())
            assert len(row) == len(self.csv_header())
            writer.writerow(
                [_val2str(val).rjust(space) for val, space in zip(row, spaces)]
            )

    @enforce_types
    def load_csv(self) -> pd.DataFrame:
        """Load csv as a pandas Dataframe."""
        df = pd.read_csv(self.csv_file)
        df.rename(columns=lambda x: x.strip(), inplace=True)  # strip whitespace
        return df
