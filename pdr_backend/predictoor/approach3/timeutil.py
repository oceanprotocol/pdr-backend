import datetime
from datetime import timezone

from enforce_typing import enforce_types


@enforce_types
def pretty_timestr(ut: int) -> str:
    """Pretty-print version of ut timestamp: show as unix time and datetime"""
    return f"timestamp={ut}, dt={ut_to_dt(ut)}"


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
      '2022-03-29_17:55' --> 1648872899300
      '2022-03-29' --> 1648872899000
    Does not use local time, rather always uses UTC
    """
    if timestr.lower() == "now":
        return current_ut()

    ncolon = timestr.count(":")
    if ncolon == 1:
        dt = datetime.datetime.strptime(timestr, "%Y-%m-%d_%H:%M")
    elif ncolon == 2:
        dt = datetime.datetime.strptime(timestr, "%Y-%m-%d_%H:%M:%S")
    else:
        dt = datetime.datetime.strptime(timestr, "%Y-%m-%d")

    dt = dt.replace(tzinfo=timezone.utc)  # tack on timezone
    return dt_to_ut(dt)


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
