import mimetypes
import magic
import base64
import io


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

