import os

import numpy as np
from enforce_typing import enforce_types

from pdr_backend.util.strutil import StrMixin


@enforce_types
class XpmtSS(StrMixin):
    __STR_OBJDIR__ = ["d"]

    def __init__(self, d: dict):
        self.d = d  # yaml_dict["xpmt_ss"]

        # handle log_dir
        assert self.log_dir == os.path.abspath(self.log_dir)
        if not os.path.exists(self.log_dir):
            print(f"Could not find log dir, creating one at: {self.log_dir}")
            os.makedirs(self.log_dir)

        if not (0 < int(self.test_n) < np.inf):  # pylint: disable=superfluous-parens
            raise ValueError(f"test_n={self.test_n}, must be an int >0 and <inf")

    # --------------------------------
    # properties direct from yaml dict
    @property
    def do_plot(self) -> bool:
        return self.d["do_plot"]

    @property
    def log_dir(self) -> str:
        s = self.d["log_dir"]
        if s != os.path.abspath(s):  # rel path given; needs an abs path
            return os.path.abspath(s)
        # abs path given
        return s

    @property
    def test_n(self) -> int:
        return self.d["test_n"]  # eg 200
