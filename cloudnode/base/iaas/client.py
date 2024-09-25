from cloudnode.base.core.lightweight_utilities.parallel import ParallelClient
from cloudnode.base.core.lightweight_utilities.filesystem import FileSystem
from enum import Enum
import time
import json
import requests

from cloudnode.base.core.lightweight_utilities.profiler_logger import ProfilerLogger
profiler, logger = ProfilerLogger.getLogger(__name__)


class ReturnType(Enum):
    """Marshalling system for r.text values in response to client."""

    STRING = 0  # r.text is any string, no processing will be done
    FILE = 1    # r.text is a stub, and will be downloaded into a ByteIO
    LIST_OF_FILES = 2   # r.text is a json of a list of stubs; unwrapped, each will be downloaded into their own BytesIO
    FILE_OF_JSON = 3    # r.text is a stub pointing to a file with a json string; will be downloaded and unwrapped
    LIST_OF_FILES_OF_JSON = 4   # r.text is a json of list of stubs; unwrapped, each downloaded and unwrapped.
    JSON = 5    # r.text is a string json, and will be unwrapped.
    LIST_OF_JSONS = 6   # r.text is a json of a list of strings, unwrapped, and each item in list will be unwrapped.


class GenericResponse:

    def __init__(self, code, data=None, error=None):
        self.success = code == 200
        self.code = code
        self.data = data
        self.error = error


class GenericCloudClient(object):

    @staticmethod
    def request(endpoint, d=None, rtype=None, method="POST"):
        """Transacts with generic backends and REST APIs with additional marshalling to return response data objects."""
        # NOTE: REST APIs return strings as their payload, and we want this request client to handle their conversions
        # automatically, i.e., to download stubs into file_objs, or json the dictionary data into a dictionary. But we
        # also want to handle errors in a way which shields users from its particulars unless they want those; so for
        # that reason we create a GenericResponse class with .success and .data and auxiliary .error and so forth.
        # NOTE: Returns None upon error.
        # NOTE: https://stackoverflow.com/questions/16511337/correct-way-to-try-except-using-python-requests-module
        r, s = None, time.time()
        try:
            if not (rtype is None or isinstance(rtype, ReturnType)):
                raise ValueError(f"rtype must be one of: {', '.join([str(e) for e in ReturnType])}")
            logger.info(f"Endpoint: {endpoint} with data={d}")

            if method == "GET":  r = requests.get(endpoint, params=d)
            elif method == "POST": r = requests.post(f"{endpoint}", json=d)  # Documentation says supports json=None.
            else: raise ValueError(f"unsupported method={method}")
            r.raise_for_status()
            rtext = r.text

            logger.info(f"Status Code: {r.status_code}, Response: {rtext}")
            if rtype is None: data = rtext
            else: data = GenericCloudClient._marshal_response_text_into_object(rtext, rtype)
            logger.info(f"Endpoint Complete: {time.time()-s:.03f} seconds: {endpoint} with data={d}")
            return GenericResponse(code=200, data=data)
        except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as e:
            msg = str(e)
            if hasattr(e.response, "text") and e.response.status_code != 404: msg += f" ==> {e.response.text}"
            logger.error(msg)
        except Exception as e:
            msg = f"GenericCloudClient request failed:\n {e}"
            if hasattr(e, "response") and hasattr(e.response, "text"): msg += f" ==> {e.response.text}"
            logger.exception(msg)
        return GenericResponse(code=r.status_code, error=msg)

    @staticmethod
    def _marshal_response_text_into_object(rtext, rtype):
        if rtype is None or rtype == ReturnType.STRING:
            return_value = rtext
        elif rtype == ReturnType.FILE:
            return_value = FileSystem.easy_download(rtext)
        elif rtype == ReturnType.LIST_OF_FILES:
            stubs = json.loads(rtext)
            return_value = ParallelClient.mapreduce(FileSystem.easy_download, list(zip(stubs)))
        elif rtype == ReturnType.FILE_OF_JSON:
            return_value = json.load(FileSystem.easy_download(rtext))
        elif rtype == ReturnType.LIST_OF_FILES_OF_JSON:
            stubs = json.loads(rtext)
            jsons = ParallelClient.mapreduce(FileSystem.easy_download, list(zip(stubs)))
            return_value = [json.load(j) for j in jsons]
        elif rtype == ReturnType.JSON:
            return_value = json.loads(rtext)
        elif rtype == ReturnType.LIST_OF_JSONS:
            jsons = json.loads(rtext)
            return_value = [json.loads(j) for j in jsons]
        else: raise RuntimeError("An unknown error occurred: return type not understood. This error should not occur.")
        return return_value
