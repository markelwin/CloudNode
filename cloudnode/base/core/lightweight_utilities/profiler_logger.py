import datetime
import time

import logging
logger = logging.getLogger(__name__)


class ProfilerLogger(object):
    """ProfilerLogger is an easy way to globally monitor operations for performance issues as a context manager."""

    def __init__(self, name):
        self.name = name

    @staticmethod
    def getLogger(name):
        """Entry point for creating a ProfilerLogger; also returns system logger for one-line convenience."""
        # SEE NOTE FTW1: if name not in logs: logs[name] = dict()
        return ProfilerLogger(name), logging.getLogger(name)

    def profile(self, context_name):
        """.profile returns a context manager which initiates a logging session for the execution within its context"""
        return _ProfilerLoggerAsContextManager(self.name, context_name)


########################################################################################################################
# internal system code below this line
########################################################################################################################

class _ProfilerLoggerAsContextManager(object):

    def __init__(self, name, context_instance):
        self.name = name
        self.domain = context_instance.upper()
        self.quants = dict()
        self.quants_as_rates = dict()

    def __enter__(self):
        self.s = time.time()
        logger.info(f"ENTERING {self.domain} at {datetime.datetime.fromtimestamp(self.s).isoformat()}")
        return self

    def add(self, quants=None, as_rates=None):
        """add measured quantities for future storage of performance statistics for monitoring and analysis"""
        if quants is not None: self.quants.update(quants)
        if as_rates is not None: self.quants_as_rates.update(as_rates)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None: return  # FIXME: Does this need production error checking etc?
        now = time.time()
        duration_s = now - self.s
        self.quants["start_dt"] = datetime.datetime.fromtimestamp(self.s).isoformat()
        self.quants["duration_s"] = duration_s
        # calculate quantities as rates if any are requested
        for name, value in self.quants_as_rates.items():
            self.quants[name] = value
            self.quants[f"{name}_per_s"] = value / duration_s
        # store the results in a global logs variable for persistent storage and future analysis
        # if self.domain not in logs[self.name]: logs[self.name][self.domain] = []  # NOTE FTW1 on pause
        # logs[self.name][self.domain].append(self.quants)
        dt_end = datetime.datetime.fromtimestamp(now).isoformat()
        logger.info(f" EXITING {self.domain} at {dt_end} after {duration_s:03f} s ==> {self.quants}")
