import os

from enforce_typing import enforce_types

from pdr_backend.util.strutil import StrMixin


@enforce_types
class SimSS(StrMixin):
    """User-controllable strategy params related to the simulation itself"""

    def __init__(self, do_plot: bool, logpath: str):
        assert os.path.exists(logpath)

        self.do_plot = do_plot
        self.logpath = logpath  # directory, not file
