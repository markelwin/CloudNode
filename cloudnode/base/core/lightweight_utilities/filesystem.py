from cloudnode.base.core.lightweight_utilities.files import construct_data_uri, convert_uri_to_bytesio
import requests
import time
import os
import io

import logging
logger = logging.getLogger(__name__)

handlers = {}  # http://, https://, file://, data:// added at prefix of file


class FileSystem(object):
    """FileSystem is the primary stub i/o for local files, urls, cloud storage from a unified entry point."""

    @staticmethod
    def protocols():
        for protocol, handler in handlers.items():
            logger.info(f"protocol={protocol} description={handler.description}")

    @staticmethod
    def easy_exists(stub):
        """Easily identify whether a stub exist."""
        for protocol, handler in handlers.items():
            if stub.lower().startswith(protocol):
                return handler.exists(stub)
        raise FileNotFoundError(f"Stub does not conform to known protocols {list(handlers.keys())}: {stub}")

    @staticmethod
    def easy_upload(file_obj, stub):
        """Easily upload a file_obj to a stub."""
        for protocol, handler in handlers.items():
            if stub.lower().startswith(protocol):
                return handler.upload(file_obj, stub)
        raise FileNotFoundError(f"Stub does not conform to known protocols {list(handlers.keys())}: {stub}")

    @staticmethod
    def easy_download(stub):
        """Easily download a stub to a file_obj"""
        for protocol, handler in handlers.items():
            if stub.lower().startswith(protocol):
                return handler.download(stub, io.BytesIO())
        raise FileNotFoundError(f"Stub does not conform to known protocols {list(handlers.keys())}: {stub}")

    @staticmethod
    def easy_listdir(directory):
        """Easily list the stubs in a directory"""
        for protocol, handler in handlers.items():
            if directory.lower().startswith(protocol):
                return handler.listdir(directory)
        raise FileNotFoundError(f"Directory does not conform to known stub protocols {list(handlers.keys())}: {directory}")

    @staticmethod
    def easy_delete(stub):
        """Easily delete a stub"""
        for protocol, handler in handlers.items():
            if stub.lower().startswith(protocol):
                return handler.delete(stub)
        raise FileNotFoundError(f"Stub does not conform to known protocols {list(handlers.keys())}: {stub}")


########################################################################################################################
# internal system code below this line
########################################################################################################################
class Handler(object):

    description = "no description provided for this protocol handler"
    @staticmethod
    def delete(stub): raise NotImplementedError("protocol does not supported delete operation.")
    @staticmethod
    def upload(source_file_obj, stub): raise NotImplementedError("protocol does not supported upload operation.")
    @staticmethod
    def listdir(directory): raise NotImplementedError("protocol does not supported listdir operation.")


class HttpStubHandler(Handler):
    """Stub handler for HTTP and HTTPS protocols: download and exists modes supported only."""

    browser_headers = {'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'}
    stub_protocols = ["https://", "http://"]
    description = "http:// and https:// url addresses: download and exists modes supported only."

    @staticmethod
    def exists(stub):
        """Returns True if a Web object exists."""
        logger.info(f"checking URL exists: {stub}")
        response = requests.get(stub)
        return response.ok

    @staticmethod
    def download(stub, destination_file_obj=None, rewind=True):
        """Downloads url from the web to the provided file_obj. Rewind will seek(0)."""
        if destination_file_obj is None: destination_file_obj = io.BytesIO()
        s = time.time()
        response = requests.get(stub, headers=HttpStubHandler.browser_headers)
        destination_file_obj.write(response.content)
        if rewind: destination_file_obj.seek(0)
        logger.info(f"File downloaded duration={time.time()-s}.")
        return destination_file_obj


class LocalFileStubHandler(Handler):
    """Stub handler for local files: download is load and upload is save."""

    stub_protocol = "file://"
    description = "Local filesystem: download is load and upload is save."

    @staticmethod
    def _parse_stub(stub):
        """Converts file://filename to filename."""
        return stub[len(LocalFileStubHandler.stub_protocol):]

    @staticmethod
    def exists(stub):
        """Returns True if a File exists."""
        logger.info(f"checking File exists: {stub}")
        filename = LocalFileStubHandler._parse_stub(stub)
        return os.path.exists(filename)

    @staticmethod
    def listdir(directory):
        """Returns list of basenames which exist in the directory."""
        directory = LocalFileStubHandler._parse_stub(directory)
        return [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

    @staticmethod
    def delete(stub):
        """Deletes a File from the local filesystem."""
        filename = LocalFileStubHandler._parse_stub(stub)
        os.remove(filename)
        logger.info(f"File {stub} deleted.")

    @staticmethod
    def download(stub, destination_file_obj=None, rewind=True):
        """Loads a filename to the provided file_obj. Rewind will seek(0)."""
        if destination_file_obj is None: destination_file_obj = io.BytesIO()
        s = time.time()
        filename = LocalFileStubHandler._parse_stub(stub)
        mode = "r" if isinstance(destination_file_obj, io.StringIO) else "rb"
        with open(filename, mode) as local_file:
            destination_file_obj.write(local_file.read())
            if rewind: destination_file_obj.seek(0)
        logger.info(f"File loaded duration={time.time()-s}.")
        return destination_file_obj

    @staticmethod
    def upload(source_file_obj, stub):
        """Saves a file_obj to local filename"""
        s = time.time()
        filename = LocalFileStubHandler._parse_stub(stub)
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        mode = "w" if isinstance(source_file_obj, io.StringIO) else "wb"
        with open(filename, mode) as local_file: local_file.write(source_file_obj.getvalue())
        logger.info(f"File saved duration={time.time()-s}")
        return stub


class DataUriStubHandler(Handler):
    """FileSystem-like handler for data URIs defined by RFC 2397 August 1998, those typical in URI of HTTP requests."""

    stub_protocol = "uri://"
    description = "data URIs defined by RFC 2397 August 1998: upload creates and download converts to bytes_io"

    @staticmethod
    def _parse_stub(stub):
        """Converts uri://data stub to return only the relevant data."""
        return stub[len(DataUriStubHandler.stub_protocol):]

    @staticmethod
    def exists(stub):
        """DataUri always exist in line; so always returns true. Syntax failures fail at actions; not if exists"""
        return True

    @staticmethod
    def download(stub, destination_file_obj=None, rewind=True):
        """Converts DataURI to BytesIO. Rewind will seek(0)."""
        s = time.time()
        data = DataUriStubHandler._parse_stub(stub)
        file_obj, suffix, attributes = convert_uri_to_bytesio(data)
        if destination_file_obj is not None: destination_file_obj.write(file_obj.getvalue())
        else: destination_file_obj = file_obj
        if rewind: destination_file_obj.seek(0)
        logger.info(f"URI converted duration={time.time()-s}.")
        return destination_file_obj

    @staticmethod
    def upload(source_file_obj, stub):
        """Converts BytesIO to DataUri. Please use stub to express ext type, i.e., 'png'."""
        if stub is not None: raise ValueError("Stub should be None; to verify user understands uris use no stubs.")
        s = time.time()
        data_uri = DataUriStubHandler.stub_protocol + construct_data_uri(source_file_obj)
        logger.info(f"URI created duration={time.time()-s}")
        return data_uri


# Adds default stub handlers (HTTP, HTTPS, FILE) to handlers.
for p in HttpStubHandler.stub_protocols: handlers[p] = HttpStubHandler()
handlers[LocalFileStubHandler.stub_protocol] = LocalFileStubHandler()
handlers[DataUriStubHandler.stub_protocol] = DataUriStubHandler()


