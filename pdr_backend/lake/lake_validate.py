import logging

import polars as pl
from enforce_typing import enforce_types

from pdr_backend.lake.lake_info import LakeInfo

pl.Config.set_tbl_hide_dataframe_shape(True)

logger = logging.getLogger("LakeValidate")


@enforce_types
class LakeValidate(LakeInfo):
    def print_results(self):
        """
        description:
            The print statement should be formatted as follows:
            # loop results
            #   print message with: (1) key, (2) error/success, (3) message
            # print num errors, num successes, and total
        """
        violations = [
            result for result in self.validation_results.values() if result is not None
        ]
        num_violations = 0

        for key, (violations) in self.validation_results.items():
            if violations is None or len(violations) == 0:
                print(f"[{key}] Validation Successful")
                continue

            print(f"[{key}] Validation Errors:")
            num_violations += len(violations)
            for violation in violations:
                print(f"> {violation}")

        print(f"Num violations: {num_violations}")

    @enforce_types
    def run(self):
        self.generate()
        self.print_results()
