import os

from enforce_typing import enforce_types

from pdr_backend.util.strutil import StrMixin


@enforce_types
class SimSS(StrMixin):
    __STR_OBJDIR__ = ["d"]

    def __init__(self, d: dict):
        self.d = d  # yaml_dict["sim_ss"]

        # handle log_dir
        assert self.log_dir == os.path.abspath(self.log_dir)
        if not os.path.exists(self.log_dir):
            print(f"Could not find log dir, creating one at: {self.log_dir}")
            os.makedirs(self.log_dir)

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
