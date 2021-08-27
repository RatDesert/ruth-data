from . import settings

# class TimestampError(Exception):
# pass
INT32_MAX = 2147483647
INT32_MIN = -INT32_MAX - 1
INT64_MAX = 9223372036854775807
INT64_MIN = -INT64_MAX - 1

class Throttled(Exception):
    pass

def throttle(previous_message_timestammp, message_timestamp):
    if (
        message_timestamp - previous_message_timestammp
    ) < settings.Message.MIN_DELAY:
        raise Throttled("Maximum sending rate exceeded.")

def ispint32(x) -> bool:
    try:
        a = float(x)
        b = int(a)
    except (TypeError, ValueError):
        return False
    else:
        return (a == b) and (0 < b < INT32_MAX)
