import importlib
import sys

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
