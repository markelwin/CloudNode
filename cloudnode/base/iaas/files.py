from cloudnode.base.core.lightweight_utilities.cloudnode import create_programmatic_directory
from cloudnode.base.core.lightweight_utilities.files import get_mime_file_obj
from cloudnode.config import RuntimeConfig
import hashlib
import io
import os


class HeavyData(object):
    """Early iteration of context-less file storage"""

    def __init__(self, file_obj, suffix=None):
        md5 = hashlib.md5(file_obj.getvalue()).hexdigest()
        if suffix is None:
            mime = get_mime_file_obj(file_obj)
            suffix = "." + mime.split("/")[1]
        directory = create_programmatic_directory(RuntimeConfig.directory_base_local, dict(_subsystem="heavydata"))
        self.name = os.path.join(directory, f"{md5}{suffix}")
        self.is_bytes = not isinstance(file_obj, io.StringIO)
        self.file_obj = file_obj

    def save(self):
        mode = "wb" if self.is_bytes else "w"
        os.makedirs(os.path.dirname(self.name), exist_ok=True)
        with open(self.name, mode) as f: f.write(self.file_obj.getvalue())
        return self
