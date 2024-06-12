from typing import Union

from enforce_typing import enforce_types
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import interpolate, stats
from scipy.special import ndtr


@enforce_types
class DistPlotdataFactory:

    @classmethod
    def build(cls, x):
        return DistPlotdata(x)


class DistPlotdata:

    @enforce_types
    def __init__(self, x: Union[list, np.ndarray]):
        if isinstance(x, np.ndarray):
            assert len(x.shape) == 1

        # base data: x, x_mesh, y_jitter
        self.x = sorted(x)
        mean, std = np.mean(x), np.std(x)
        self.x_mesh = np.linspace(min(x) - std, max(x) + std, num=200)
        self.y_jitter = _get_jitter(len(x))

        # pdf: raw data counted (=histogram)
        nbins = max(3, min(100, len(x) // 5))
        self.counts, bins = np.histogram(x, bins=nbins)
        self.bins = 0.5 * (bins[:-1] + bins[1:])
        self.bar_width = bins[1] - bins[0]

        # pdf: normal est
        self.ypdf_normal_mesh = stats.norm.pdf(self.x_mesh, mean, std)

        # pdf: kde est
        kde_model = stats.gaussian_kde(x)
        self.ypdf_kde_mesh = kde_model.evaluate(self.x_mesh)

        # cdf: raw data counted
        self.ycdf_raw = np.linspace(0.0, 1.0, len(x))

        # cdf: normal est
        self.ycdf_normal_mesh = stats.norm.cdf(self.x_mesh, mean, std)

        # cdf: kde est
        # https://stackoverflow.com/a/71993662
        self.ycdf_kde_mesh = [
            ndtr(np.ravel(x_item - kde_model.dataset) / kde_model.factor).mean()
            for x_item in self.x_mesh
        ]

        # nq: raw data counted
        # self.ynq_raw = FIXME

        # nq: normal est
        # self.ynq_normal_mesh = FIXME

        # nq: kde est
        # https://stackoverflow.com/a/71993662
        x2, y2 = [], []
        for xi, yi in zip(self.x_mesh, self.ycdf_kde_mesh):
            if xi not in x2 and yi not in y2:
                x2.append(xi)
                y2.append(yi)
        assert _all_unique(x2)
        assert _all_unique(y2)
        inversefunction = interpolate.interp1d(y2, x2, kind="cubic", bounds_error=False)
        self.ynq_kde_mesh = inversefunction(self.x_mesh)

        y_jitter = -_get_jitter(len(x)) * 0.25 - 0.01

    @property
    def max_density_est(self) -> float:
        return max(max(self.ypdf_normal_mesh), max(self.ypdf_kde_mesh))


J = np.array([], dtype=float)  # jitter


@enforce_types
def _get_jitter(N: int) -> np.ndarray:
    global J
    while J.shape[0] < N:
        J = np.append(J, np.random.rand())
    return J[:N]


@enforce_types
def _all_unique(x) -> bool:
    """Returns True if all items in x are unique"""
    return len(set(x)) == len(x)
