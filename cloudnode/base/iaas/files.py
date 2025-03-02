from cloudnode.config import RuntimeConfig
import tempfile
import hashlib
import io
import os


class HeavyData(object):
    """Early iteration of context-less file storage"""

    def __init__(self, file_obj, basename=None, add_md5=False, tags=None, suffix=None, temporary=False, exist_ok=True):
        # HeavyData stores a file at: <basename>.k1=v1.k2=v2.md5=<md5><suffix>
        if tags is None: tags = dict()
        if add_md5: tags.update(dict(md5=hashlib.md5(file_obj.getvalue()).hexdigest()))

        self.tags = tags
        self.filename = HeavyData.make_filename(basename, tags, suffix, temporary)
        if os.path.exists(self.filename) and not exist_ok: raise RuntimeError(f"already exists path={self.filename}")
        self.is_bytes = not isinstance(file_obj, io.StringIO)
        self.file_obj = file_obj

    @staticmethod
    def make_filename(basename=None, tags=None, suffix=None, temporary=False):
        basename = "" if basename is None else basename
        if len(tags) != 0:
            if len(basename) != 0: basename += "."
            basename += ".".join([f"{k}={v}" for k,v in tags.items()])
        if suffix is not None: basename += suffix
        directory = tempfile.gettempdir() if temporary else RuntimeConfig.directory_base_local
        directory = os.path.join(directory, "_subsystem/heavydata/")
        return os.path.join(directory, basename)

    def save(self):
        mode = "wb" if self.is_bytes else "w"
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)
        with open(self.filename, mode) as f: f.write(self.file_obj.getvalue())
        return self

    @staticmethod
    def copy_from(filename, is_bytes=True, add_md5=False, tags=None, temporary=False, exist_ok=True):
        mode = "rb" if is_bytes else "r"
        file_obj = io.BytesIO() if is_bytes else io.StringIO()
        with open(filename, mode) as f: file_obj.write(f.read())
        basename, suffix = os.path.splitext(os.path.basename(filename))
        return HeavyData(file_obj, basename=basename, add_md5=add_md5, tags=tags, suffix=suffix, temporary=temporary, exist_ok=exist_ok).save()
