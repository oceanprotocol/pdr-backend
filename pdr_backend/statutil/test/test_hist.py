from enforce_typing import enforce_types
import numpy as np

from pdr_backend.statutil.hist import plot_hist

SHOW_PLOT = False  # only turn on for manual testing


@enforce_types
def test_hist_SHOW_PLOT():
    """SHOW_PLOT should only be set to True temporarily in local testing."""
    assert not SHOW_PLOT


@enforce_types
def test_hist():
    y1 = 1.0 + 2.0 * np.random.randn(100)
    y2 = 10.0 + 5.0 * np.random.randn(100)
    y = list(y1) + list(y2)

    fig = plot_hist(y)
    if SHOW_PLOT:
        fig.show()
