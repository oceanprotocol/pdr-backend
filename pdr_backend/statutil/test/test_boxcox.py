#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os
from enforce_typing import enforce_types
from scipy import stats

from pdr_backend.lake.test.resources2_btc import BTC_history
from pdr_backend.statutil.dist_plotter import plot_dist
from pdr_backend.statutil.boxcox import safe_boxcox

# set env variable as true to show plots
SHOW_PLOT = os.getenv("SHOW_PLOT", "false").lower() == "true"


@enforce_types
def test_safe_boxcox():
    y: list = BTC_history()  # 5050 historical values of BTC, eg $60234.23
    if SHOW_PLOT:
        fig = plot_dist(y, True, False, False)
        fig.update_layout(title="original")
        fig.show()

    # y_bc should not come out constant. But with stats.boxcox it does, yikes
    # -> we encountered this problem in issue #1174
    y_bc, _ = stats.boxcox(y)
    assert min(y_bc) == max(y_bc)  # unwanted behavior, but a reality

    # safe_boxcox applies boxcox *safely*
    y_bc2 = safe_boxcox(y)
    assert min(y_bc2) != max(y_bc2)
    if SHOW_PLOT:
        fig = plot_dist(y_bc2, True, False, False)
        fig.update_layout(title="safe box-cox transformed")
        fig.show()
