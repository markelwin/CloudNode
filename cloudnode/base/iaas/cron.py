# from cloudnode.base.iaas.client import AetherClient
import threading
import time

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FIXME: genericcloudclient not set up yet.


class EasyCron(object):
    """Simply makes a GenericCloudClient call if n_seconds have passed since the last call."""

    def __init__(self, endpoint, every_s, data=None):
        self.endpoint = endpoint
        self.data = dict() if data is None else data
        self.every_s = every_s
        self.last_request_s = None
        self.thread = None

    def do_if_time_has_lapsed(self):
        now = time.time()
        if self.last_request_s is None or now >= self.last_request_s + self.every_s:
            self.last_request_s = now
            if self.thread is not None and self.thread.is_alive():
                # if previous thread is still running, it will continue to run, but alert the system.
                logger.warning(f"CRON has still running thread: last_request_s={self.last_request_s}: {self.endpoint} data={self.data}")
            logger.info(f"CRON at {now} every_s={self.every_s}: {self.endpoint} data={self.data}")
            self.thread = threading.Thread(target=AetherClient.request, args=(self.endpoint, self.data, None),
                                           name=f"cron={self.endpoint}_ts={now}", daemon=True)
            self.thread.start()
