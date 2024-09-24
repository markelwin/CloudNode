import datetime

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NFSysops:

    @staticmethod
    def system_healthcheck(): return dict(now=datetime.datetime.now().isoformat())

