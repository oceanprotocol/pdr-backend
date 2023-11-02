from datetime import datetime, timedelta
from typing import Tuple


def get_start_end_params(contract_timeframe: str) -> Tuple[int, int]:
    """
    Returns a tuple of Unix timestamps. The first value is the timestamp
    for one week ago, and the second value is the current timestamp.

    Returns:
        Tuple[int, int]: (start_ts, end_ts)
    """
    end_ts = int(datetime.utcnow().timestamp())
    time_delta = (
        timedelta(weeks=2) if contract_timeframe == "5m" else timedelta(weeks=4)
    )
    start_ts = int((datetime.utcnow() - time_delta).timestamp())

    return start_ts, end_ts
