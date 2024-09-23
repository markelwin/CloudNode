# import zipfile
import tempfile
import mimetypes
import magic
import base64
import io
# import os


def get_mime_file_obj(file_obj):
    """Uses python-magic to estimate file_obj mime type from its early bytes data"""
    file_obj.seek(0)
    mime = magic.from_buffer(file_obj.read(2048), mime=True)
    file_obj.seek(0)
    return mime


def construct_data_uri(file_obj, attributes=None):
    """Converts a BytesIO into a base64 encoded data_uri"""
    mime = get_mime_file_obj(file_obj)
    a_s = "" if attributes is None else ";".join([f"{k}={v}" for k,v in attributes.items()]) + ";"
    return f'data:{mime};{a_s}base64,' + base64.b64encode(file_obj.getvalue()).decode("utf-8")


def convert_uri_to_bytesio(data_uri):
    """Converts an DataURI into a file_obj, and its extension and attributes."""
    middle = data_uri.split(":")[1].split(",")[0]
    parts = middle.split(";")
    suffix = mimetypes.guess_extension(parts[0])
    attributes = [m.split("=") for m in parts[1:-1]]
    attributes = {k: v for k, v in attributes}
    data = data_uri.split(",")[1]
    file_obj = io.BytesIO()
    file_obj.write(base64.decodebytes(bytes(data, "utf-8")))
    return file_obj, suffix, attributes


class IaasTemporaryFile(object):
    """The IaasTemporaryFile ensures temporary files are always deleted; expecting users to load file into bytes_io."""
    # NOTE: NamedTemporaryFile is a function, not a class, which creates a _TemporaryFileWrapper; cannot be subclassed.
    # There are workarounds that can monkey-patch the _TemporaryFileWrapper methods and attributes, i.e. .name and so on
    # However, these appear unstable, and until attributes other than .name are necessary, we will create a new class.

    def __init__(self, **kwargs):
        """The __init__ file contains all the functionality of tempfile.NamedTemporaryFile except asserts delete=True"""
        kwargs["delete"] = True
        self._tmp = tempfile.NamedTemporaryFile(**kwargs)
        self.name = self._tmp.name

    def load(self, file_obj):
        """Writes the file_obj to the file; allows user to load file_obj at initialization time in one line."""
        mode = "wb" if isinstance(file_obj, io.BytesIO) else "w"
        with open(self.name, mode) as file: file.write(file_obj.getvalue())
        return self

    def load_filename(self, filename):
        with open(filename, "rb") as file_to_read:
            with open(self.name, "wb") as file:
                file.write(file_to_read.read())
        return self

    def as_bytes_io(self, as_stringio=False):
        """Returns the user a BytesIO file with temporary file contents loaded, and rewound to beginning of file."""
        file_obj = io.StringIO() if as_stringio else io.BytesIO()
        mode = "rb" if isinstance(file_obj, io.BytesIO) else "r"
        with open(self.name, mode) as f: file_obj.write(f.read())
        file_obj.seek(0)
        return file_obj

    # def as_zip_obj(self, pwd=None):
    #     tmp = IaasTemporaryFile(suffix=".zip")
    #     ZipUtils.zip_files(self.name, tmp.name, pwd=pwd)
    #     return tmp.as_bytes_io()


# class ZipUtils(object):
#
#     @staticmethod
#     def zip_files(filenames, out_filename, pwd=None, flatten_dirs=True):
#         _to_name = [os.path.basename(fn) for fn in filenames] if flatten_dirs else filenames
#         with zipfile.ZipFile(out_filename, 'w', zipfile.ZIP_DEFLATED) as z:
#             for i, filename in enumerate(filenames): z.write(filename, arcname=_to_name[i])
#             if pwd is not None: z.setpassword(pwd.encode())
#
#     @staticmethod
#     def unzip_into_dir(zip_file, into_dir, pwd=None):
#         with zipfile.ZipFile(zip_file, 'r') as z:
#             z.extractall(into_dir, pwd=pwd)


