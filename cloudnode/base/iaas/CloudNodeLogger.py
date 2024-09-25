from cloudnode import SwiftData, sd
import dataclasses
import time

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# The CloudNodeLogger is a simple logger designed to buffer and write to disk each log statement, in addition to pushing
# statements to standard-output; the purpose of this logger is to wrap TraditionalCloudFunctions so that users may write
# their functions with standard logging capabilities, and the IAAS framework elevates these to cloud stage logging here.
# The CloudNodeLogger may accept an optional runtime state upon creation to describe the context of the CloudFunction,
# i.e., defining a process id, or any other information which may be useful for tracing Functions across one another.

index = "cloudnode.cloudnodelogger"  # FIXME: This should be system defined.


@dataclasses.dataclass
class LogLine(SwiftData):
    function: sd.string()
    pid: sd.string()
    level: sd.string()
    timestamp: sd.timestamp()
    module: sd.string()
    line: sd.integer()
    message: sd.string(analyze=True)


class CloudNodeLoggerHandler(logging.StreamHandler):

    write_to_disk_every_s = 60

    def __init__(self, pid=None):
        super(CloudNodeLoggerHandler, self).__init__()
        self.pid = pid
        _formatter = logging.Formatter(f"%(levelname)s:pid={self.pid}:%(name)s:%(message)s")
        self.setFormatter(_formatter)
        self.buffer = []
        self.start_s = time.time()
        self.last_handle_every_s = None

    def handle_every_s_if_necessary(self):
        if self.last_handle_every_s is None or time.time() - self.last_handle_every_s > CloudNodeLoggerHandler.write_to_disk_every_s:
            failed = []
            # for args in self.buffer:
            #     try: LogLine.new(**args).save(index)
            #     except: failed.append(args)
            if len(failed) != 0: logger.warning(f"cloudnodelogger failed to save records n={len(failed)}")
            self.buffer = failed
            self.last_handle_every_s = time.time()

    def emit(self, record):
        """This is the standard method for what to do with a new inbound log request."""
        try:
            super(CloudNodeLoggerHandler, self).emit(record)  # call the default logger method (i.e., to stdout)
            args = dict(level=record.levelname, timestamp=record.created, logger=record.name,
                        module=record.module, line=record.lineno, message=record.msg, pid=self.pid)
            self.buffer.append(args)
            self.handle_every_s_if_necessary()
        except (KeyboardInterrupt, SystemExit): raise
        except: self.handleError(record)  # if an error propagate its exceptions using the standard default methods


class CloudNodeLogger(logging.RootLogger):

    def __init__(self, pid=None):
        super(CloudNodeLogger, self).__init__(logging.getLogger().level)
        self.original_handlers = []
        self.pid = pid
        self.cloud_handler = CloudNodeLoggerHandler(pid=pid)

    def __enter__(self):  # get the handlers attached to the original root logger; reattach after .exit()
        _logger = logging.getLogger()
        for h in _logger.handlers: self.original_handlers.append(h)
        _logger.handlers.clear()
        _logger.addHandler(self.cloud_handler)  # remove all handlers, and add only the new cloud_logger
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _logger = logging.getLogger()
        _logger.handlers.clear()
        for h in self.original_handlers: _logger.addHandler(h)  # remove all once again, and add back original handlers



# state = dict(node="FunctionName", pid="asdfg", tid="fgaer", uuid="_MACHINE", fid="aewrt")
# with CloudNodeLogger(pid=state["pid") as logger:
#     for i in range(30):
#         logger.info(f"This message is at {2*i} seconds.")
#         time.sleep(2)

