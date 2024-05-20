from pdr_backend.util.time_types import UnixTimeMs, UnixTimeS
from datetime import datetime
import time

def test_time_ms(tmpdir):
    # from lake_ss line 76
    ms_end_ts_from_timestr_now = UnixTimeMs.from_timestr("now")
    
    # from app.py line 237
    ms_end_ts_from_utc = UnixTimeMs(int(datetime.utcnow().timestamp())) #in seconds
    s_end_ts_from_utc = UnixTimeS(int(datetime.utcnow().timestamp())) #in seconds
    
    # unix timestamp
    print(">>> ms_end_ts_from_timestr_now", ms_end_ts_from_timestr_now)
    
    # timestamp from datetime utcnow()... which is in the future... and wrong
    print(">>> ms_end_ts_from_utc", ms_end_ts_from_utc)
    print(">>> s_end_ts_from_utc", s_end_ts_from_utc)
    
    # just vanilla python unix timestamp
    print(">>> time.time()", int(time.time()))

    # UnixTimeMs now
    print(">>> UnixTimeMs.now()", UnixTimeMs.now())

    # UnixTimeS now
    print(">>> UnixTimeS.now()", UnixTimeS.now())

    assert ms_end_ts_from_timestr_now > 0
    assert ms_end_ts_from_utc > 0
    assert time.time() > 0

    # Assert that unix time is in the future, from UnixTimeMs and UnixTimeS, which are local time
    assert int(time.time()) != UnixTimeMs.now().to_seconds()
    assert int(time.time()) != UnixTimeS.now()
    
    # Assert these two are the same
    assert UnixTimeMs.now().to_seconds() == UnixTimeS.now()

    # Assert whatever app.py is doing... is wrong
    assert ms_end_ts_from_utc == ms_end_ts_from_utc
    assert ms_end_ts_from_utc > UnixTimeMs.now().to_seconds()
    assert s_end_ts_from_utc > UnixTimeS.now()