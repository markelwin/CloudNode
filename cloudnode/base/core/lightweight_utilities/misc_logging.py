import time
import logging

_LOG_LEVELS = dict(DEBUG=logging.DEBUG,
                   INFO=logging.INFO,
                   WARNING=logging.WARNING,
                   ERROR=logging.ERROR)


class LogEveryN(object):
    """Publish log message every N calls to the function (any call level increments its counter)"""

    def __init__(self, _logger, n, and_first=False):
        self.logger = _logger
        self.and_first = and_first
        self.i = 0
        self.n = n

    def log(self, level, msg):
        self.i += 1
        if self.and_first or self.i >= self.n:
            self.logger.log(_LOG_LEVELS[level], msg)
            self.and_first = False
            self.i = 0


class LogEveryS(object):
    """Publishes log message if n seconds have passed since its last publishing."""
    # NOTE: because level and msg are not tracked; a new instance of class should be created for each log message.

    def __init__(self, _logger, n_sec, and_first=False):
        self.logger = _logger
        self.and_first = and_first
        self.n_sec = n_sec
        self.last_publish_s = time.time()

    def log(self, level, msg):
        now = time.time()
        if self.and_first or now >= self.last_publish_s + self.n_sec:
            self.logger.log(_LOG_LEVELS[level], msg)
            self.and_first = False
            self.last_publish_s = now

