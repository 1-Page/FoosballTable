import config
import datetime


def get_timestamp_for_now():
    return datetime.datetime.now().strftime(config.TIMESTAMP_FORMAT)


def get_seconds_from_timestamp(timestamp):
    now = datetime.datetime.now()
    then = datetime.datetime.strptime(timestamp, config.TIMESTAMP_FORMAT)
    return abs((now - then).seconds)


def seconds_string(seconds):
    return str(datetime.timedelta(seconds=seconds))
