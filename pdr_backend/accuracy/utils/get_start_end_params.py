from datetime import datetime, timedelta
from typing import Tuple

def get_start_end_params() -> Tuple[int, int]:
    """
    Returns a tuple of Unix timestamps. The first value is the timestamp
    for one week ago, and the second value is the current timestamp.

    Returns:
        Tuple[int, int]: (start_ts, end_ts)
    """
    end_ts = int(datetime.utcnow().timestamp())
    start_ts = int((datetime.utcnow() - timedelta(weeks=1)).timestamp())
    
    return start_ts, end_ts
