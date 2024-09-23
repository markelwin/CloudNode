from pathlib import Path
import os

# base operating directory: all cloudnode persistent data occurs in a subdirectory placed in this directory
dir_persistent = Path.home()


class CoreConfig(object):
    """The CoreConfig class describes application ownership and metadata."""
    repository = "cloudnode"


class RuntimeConfig(object):
    """The RuntimeConfig class describes application runtime configuration details."""
    directory_base_local = os.path.join(dir_persistent, "__cloudnode_storage/_system/cloudnode/")
