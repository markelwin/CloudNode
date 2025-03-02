from contextlib import contextmanager
import importlib
import psutil
import sys
import os

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def dynamic_variable_loader(module, variable_name):
    try:
        if module not in sys.modules: sys.modules[module] = importlib.import_module(module)
        return getattr(sys.modules[module], variable_name)
    except Exception as e:
        logger.error(f"module variable load failed: {e}", exc_info=True)
        raise

@contextmanager
def TemporarilySetEnv(**kwargs):
    """Context manager to temporarily set environment variables."""
    original_env = {key: os.environ.get(key) for key in kwargs}
    try:
        os.environ.update(kwargs)
        yield
    finally:
        for key, value in original_env.items():
            if value is None: os.environ.pop(key, None)
            else: os.environ[key] = value


def this_binary_is_running(binary):
    for process in psutil.process_iter(["name"]):
        if process.info["name"] == binary: return True
    return False
