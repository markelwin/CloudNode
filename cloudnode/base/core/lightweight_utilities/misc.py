from contextlib import contextmanager

import logging
logger = logging.getLogger(__name__)


@contextmanager
def TemporarilySuppressLoggingEqualOrHigher(supress_unless=logging.ERROR):
    """Context manager to supress logging messages less severe than the supress_unless logging level."""
    # NOTE: Useful for depending on packages that contain verbose warnings, etc., like ElasticSearch client connections.
    current_level = logging.root.manager.disable
    logging.disable(supress_unless)
    try:
        yield
    finally:
        logging.disable(current_level)
