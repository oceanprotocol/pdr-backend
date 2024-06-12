from typing import List

from enforce_typing import enforce_types
import numpy as np
from plotly.subplots import make_subplots

from pdr_backend.statutil.dist_plotdata import DistPlotdata, DistPlotdataFactory
from pdr_backend.statutil.dist_plotter import (
    add_pdf,
    add_cdf,
    add_nq,
    plot_dist,
)
from pdr_backend.statutil.test.resources import data_x

SHOW_PLOT = True  # only turn on for manual testing


@enforce_types
def test_dist_SHOW_PLOT():
    """SHOW_PLOT should only be set to True temporarily in local testing."""
    assert not SHOW_PLOT


@enforce_types
def test_plot_dist__pdf():
    x = _data1()
    fig = plot_dist(x, True, False, False)
    assert fig is not None
    if SHOW_PLOT:
        fig.show()


@enforce_types
def test_plot_dist__pdf_cdf_nq():
    x = _data1()
    fig = plot_dist(x, True, True, True)
    assert fig is not None
    if SHOW_PLOT:
        fig.show()


@enforce_types
def test_add_pdf_cdf_nq():
    x = _data1()
    d: DistPlotdata = DistPlotdataFactory.build(x)
    fig = make_subplots(rows=3, cols=1)
    add_pdf(fig, d, row=1, col=1)
    add_cdf(fig, d, row=2, col=1)
    add_nq(fig, d, row=3, col=1)
    assert fig is not None
    if SHOW_PLOT:
        fig.show()


@enforce_types
def _data1() -> List[float]:
    x1 = 1.0 + 2.0 * np.random.randn(100)
    x2 = 10.0 + 5.0 * np.random.randn(100)
    x = list(x1) + list(x2)
    return x


@enforce_types
def test_plot_dist__pdf_cdf_nq__data2():
    x = _data2()
    fig = plot_dist(x, True, True, True)
    assert fig is not None
    if SHOW_PLOT:
        fig.show()


@enforce_types
def _data2() -> List[float]:
    return data_x()
