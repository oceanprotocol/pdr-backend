TRANSITION_TOOLTIP = """
If an autoregressive model of the last 1K candles is more accurate than the last 10K candles, this means that the model parameters change. That is, the data is non-stationary. This is a problem because it means we can't make use most historical data, and so our model accuracy is limited.


Imagine if we can transform the data somehow such that historical data can be used. That is, we make the data "stationary", where the feed's dynamics (after transformation) don't change at different points in the past. Therefore we can learn models over longer time periods.


The "ADF" (Augmented Dickey-Fuller) measure tells us how stationary a feed is. We want the value to be <0.05. Any larger, and we should apply further transforms until it is stationary. (And no more transforms than needed)


The order of transforms should be: first apply BC, then D=1, then D=2. Where:
 - "BC=T/F" = Do apply Box-Cox Transform True/False? The Box-Cox transform makes the feed's values follow a more Gaussian distribution, by warping the outliers to be less outlying, as needed.
 - "D=0/1/2" = Apply no differencing (0), apply first-order differencing: "x(t-1) - x(t-2)" (trend), or apply second-order differencing "(x(t-1) - x(t-2)) - (x(t-2) - x(t-3))" (curvature).
E.g. if "BC=T, D=1" is the first transform where ADF < 0.05, then that's the transform you want to work with.


Guideline: choose the least amount of transformations to make your data stationary. When building models later, apply this transform.
"""

SEASONAL_DECOMP_TOOLTIP = """
These plots are the ARIMA-style seasonal decomposition of the (transformed) feeds.


The row 1 plot shows the relative energy (strength). The non-decomposed feed (row 2) has relative energy of 1.0, by definition. Then rows 2, 3, and 4 are the trend portion, seasonal portion, and residuals (leftovers).


The plots help you to understand the influence of trend vs seasonality (under ARIMA assumptions).
"""

AUTOCORRELATION_TOOLTIP = """
The autocorrelation (ACF) plot shows you how much a feed correlates with itself, for various lags. E.g. if it has super-high correlation at lag=5, it means that there's a large repeating component every five candles. The blue shadow shows the bounds of uncertainty. As lag increases, autocorrelation tends to decrease and uncertainty increases. If your plot doesn't extend far enough to the right to show this, then increase maximum lag.


Guideline: In your ARIMA models, the MA value should = the smallest lag where autocorrelation is finally < uncertainty shadow.


The partial autocorrelation (PACF) plot is similar to autocorrelation plots, but using partial autocorrelations.


Guideline: In your ARIMA models, the AR value should = the smallest lag where partial autocorrelation is finally < uncertainty shadow.
"""
