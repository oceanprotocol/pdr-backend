from typing import List

from enforce_typing import enforce_types
import numpy as np
from plotly.subplots import make_subplots

from pdr_backend.statutil.dist import (
    add_pdf,
    plot_pdf,
    plot_pdf_cdf_nq,
    plot_pdf_nq,
)

SHOW_PLOT = True # only turn on for manual testing


@enforce_types
def test_dist_SHOW_PLOT():
    """SHOW_PLOT should only be set to True temporarily in local testing."""
    assert not SHOW_PLOT

@enforce_types
def test_plot_pdf():
    x = _data()
    fig = plot_pdf(x)
    assert fig is not None
    if SHOW_PLOT:
        fig.show()
        
@enforce_types
def test_add_pdf():
    x = _data()
    fig = make_subplots(rows=1, cols=1)
    add_pdf(fig, x, row=1, col=1)
    assert fig is not None
    if SHOW_PLOT:
        fig.show()

        
@enforce_types
def test_plot_pdf_cdf_nq():
    x = _data()
    fig = plot_pdf_cdf_nq(x)
    assert fig is not None
    if SHOW_PLOT:
        fig.show()

        
@enforce_types
def test_plot_pdf_nq():
    x = _data()
    fig = plot_pdf_nq(x)
    assert fig is not None
    if SHOW_PLOT:
        fig.show()
        
@enforce_types
def _data() -> List[float]:
    x1 = 1.0 + 2.0 * np.random.randn(100)
    x2 = 10.0 + 5.0 * np.random.randn(100)
    x = list(x1) + list(x2)
    return x
    
