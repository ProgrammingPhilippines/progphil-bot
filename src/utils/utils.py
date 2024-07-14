import re
from datetime import datetime


def parse(timestr: str) -> int:
    """Parses a human readable time string to seconds.

    Example:
        1mt1d = 2630000 seconds

    :param timestr: The time string to parse
    """

    mapping = {
        "s": 1,
        "m": 60,
        "h": 3600,
        "d": 86400,
        "wk": 604800,
        "mt": 2628000
    }

    seconds = 0
    numstr = ""

    for t in re.split("(\d+)", timestr):
        # Split the numbers from the letters
        if t.isdigit():
            numstr += t

        if t in mapping.keys():
            # If `t` is in the keys, multiply the numstr from the value and 
            # add it to the seconds, then reset the numstr.
            seconds += int(numstr)*mapping[t]
            numstr = ""

    return seconds


def validate_time(timestr: str):
    """Checks if the time is valid.

    :param time_string: The time string. ex: 1:24, 16:23
    :return: True if the time is valid, False if not
    """

    pattern = r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$'
    return re.match(pattern, timestr)


def validate_date(datestr: str):
    """Validates if the date is valid and returns it if so.

    :param datestr: The date string to validate.
    """

    try:
        return datetime.strptime(datestr, "%m/%d/%Y").timestamp()
    except (ValueError, OSError):
        return False
