from pytz import timezone, UnknownTimeZoneError

def check_port(p):
    if p > 65535 or p <= 0:
        raise ValueError(f"Port number must be in the range 0 to 65535, not {p}")
    return p

def check_timezone(tz: str):
    try:
        timezone(tz)
    except UnknownTimeZoneError as e:
        raise ValueError(f"Timezone {tz} could not be resolved") from e
    return tz