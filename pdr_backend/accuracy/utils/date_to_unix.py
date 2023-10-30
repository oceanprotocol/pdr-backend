from datetime import datetime
import time

def date_to_unix(date_string: str) -> int:
    dt = datetime.strptime(date_string, "%Y-%m-%d")
    return int(time.mktime(dt.timetuple()))
