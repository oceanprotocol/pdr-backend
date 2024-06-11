from enforce_typing import enforce_types
import numpy as np
import plotly.express as px


@enforce_types
def plot_hist(y):
    mean, std = np.mean(y), np.std(y)

    mn = mean - 4 * std
    mx = mean + 4 * std
    fig = px.histogram(y, range_x=[mn, mx])
    fig.update_layout(showlegend=False)

    return fig
