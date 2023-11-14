import datetime
from datetime import timezone

from enforce_typing import enforce_types


@enforce_types
def pretty_timestr(ut: int) -> str:
    """Pretty-print version of ut timestamp: show as unix time and datetime"""
    return f"timestamp={ut}, dt={ut_to_timestr(ut)}"


@enforce_types
def current_ut() -> int:
    """Return the current date/time as a unix time (int in # ms)"""
    dt = datetime.datetime.now(timezone.utc)
    return dt_to_ut(dt)


@enforce_types
def timestr_to_ut(timestr: str) -> int:
    """
    Convert a datetime string to unix time (in #ms)
    Needs a date; time for a given date is optional.

    Examples:
      'now' --> 1648872899300
      '2022-03-29' --> 1648872899000 [just gave date]
      '2022-03-29_17:55' --> 1648576500000 [gave h & min too]
      '2022-03-29_17:55:12.345' -> 1648576512345 [gave s & ms too]
      '2022-03-29_17:55:12.345' -> 1648576512345 [gave s & ms too]

    Does not use local time, rather always uses UTC
    """
    if timestr.lower() == "now":
        return current_ut()

    ncolon = timestr.count(":")
    if ncolon == 0:
        dt = datetime.datetime.strptime(timestr, "%Y-%m-%d")
    elif ncolon == 1:
        dt = datetime.datetime.strptime(timestr, "%Y-%m-%d_%H:%M")
    elif ncolon == 2:
        if "." not in timestr:
            dt = datetime.datetime.strptime(timestr, "%Y-%m-%d_%H:%M:%S")
        else:
            dt = datetime.datetime.strptime(timestr, "%Y-%m-%d_%H:%M:%S.%f")
    else:
        raise ValueError(timestr)

    dt = dt.replace(tzinfo=timezone.utc)  # tack on timezone
    return dt_to_ut(dt)


@enforce_types
def ut_to_timestr(ut: int) -> str:
    """
    Convert unix time (in # ms) to datetime string.
    The datetime string will always include hh and mm.

    Examples:
      0 -> '1970-01-01_00:00:00.000' [unix start time]
      12345 -> '1970-01-01_00:00:12.345' [unix start time + 12,345 ms]
      1648576500000 -> '2022-03-29_17:55:00.000' [a modern time]
      1648576512345 -> '2022-03-29_17:55:12.345' [""]

    Does not use local time, rather always uses UTC
    """
    dt: datetime.datetime = ut_to_dt(ut)
    return dt.strftime("%Y-%m-%d_%H:%M:%S.%f")[:-3]


@enforce_types
def dt_to_ut(dt: datetime.datetime) -> int:
    """Convert datetime to unix time (int in # ms)"""
    return int(dt.timestamp() * 1000)


@enforce_types
def ut_to_dt(ut: int) -> datetime.datetime:
    """Convert unix time (in # ms) to datetime format"""
    dt = datetime.datetime.utcfromtimestamp(ut / 1000)
    dt = dt.replace(tzinfo=timezone.utc)  # tack on timezone

    # postcondition
    ut2 = int(dt.replace(tzinfo=timezone.utc).timestamp() * 1000)
    assert ut2 == ut, (ut, ut2)

    return dt


@enforce_types
def ms_to_seconds(ms: int) -> int:
    """Convert milliseconds to seconds"""
    return int(ms / 1000)
