
import config
import datetime

def getTimestampForNow():
    return datetime.datetime.now().strftime(config.TIMESTAMP_FORMAT)

def getSecondsFromTimestamp(timestamp):
    now = datetime.datetime.now()
    then = datetime.datetime.strptime(timestamp, config.TIMESTAMP_FORMAT)
    return abs((now-then).seconds)

def seconds_string(seconds):
    return str(datetime.timedelta(seconds=seconds))