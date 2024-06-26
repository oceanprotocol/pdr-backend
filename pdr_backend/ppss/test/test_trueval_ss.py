#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enforce_typing import enforce_types

from pdr_backend.ppss.trueval_ss import TruevalSS


@enforce_types
def test_trueval_ss():
    d = {
        "sleep_time": 30,
        "batch_size": 50,
        "feeds": ["binance BTC/USDT c 5m"],
    }
    ss = TruevalSS(d)
    assert ss.sleep_time == 30
    assert ss.batch_size == 50
