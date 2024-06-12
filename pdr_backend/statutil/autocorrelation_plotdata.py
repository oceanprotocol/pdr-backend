from enforce_typing import enforce_types
import numpy as np
from statsmodels.tsa.stattools import acf, adfuller, pacf


class AutocorrelationPlotdataFactory:

    @classmethod
    def build(cls, y_values, nlags: int) -> "AutocorrelationPlotdata":
        assert len(y_values.shape) == 1, "y_values must be 1d array"

        N_samples = len(y_values)
        adf_pvalue = adfuller(y_values)[1]

        target_CI = 0.95  # target 95% confidence interval
        alpha = 1.0 - target_CI
        acf_results = CorrResults(acf(y_values, nlags=nlags, alpha=alpha))
        pacf_results = CorrResults(pacf(y_values, nlags=nlags, alpha=alpha))

        plotdata = AutocorrelationPlotdata(
            N_samples,
            adf_pvalue,
            acf_results,
            pacf_results,
        )

        return plotdata


class CorrResults:
    @enforce_types
    def __init__(self, corr_results: tuple):
        """@arguments -- corr_results -- output of acf() or pacf()"""
        values = corr_results[0]
        ci_lower = np.array([pair[0] for pair in corr_results[1]])
        ci_upper = np.array([pair[1] for pair in corr_results[1]])
        ci_diff = ci_upper - ci_lower

        self.values = values
        self.lower_exclusion = -1 * ci_diff
        self.upper_exclusion = +1 * ci_diff

    @property
    def max_lag(self) -> int:
        return len(self.values)

    @property
    def x_lags(self) -> np.ndarray:
        return np.arange(0, self.max_lag)


@enforce_types
class AutocorrelationPlotdata:
    """Simple class to manage many inputs going to plot_autocorrelation."""

    def __init__(
        self,
        N_samples: int,
        adf_pvalue: float,
        acf_results: CorrResults,
        pacf_results: CorrResults,
    ):
        self.N_samples = N_samples
        self.adf_pvalue = adf_pvalue
        self.acf_results = acf_results
        self.pacf_results = pacf_results

    @property
    def max_lag(self) -> int:
        return self.acf_results.max_lag
