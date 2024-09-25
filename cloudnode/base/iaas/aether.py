from cloudnode.base.iaas.client import ReturnType, GenericCloudClient
from cloudnode.base.iaas.nodes.BuildServletConfig import BuildServletConfig
from flask import Response
import json
import uuid

from cloudnode.base.core.lightweight_utilities.profiler_logger import ProfilerLogger
profiler, logger = ProfilerLogger.getLogger(__name__)


class AetherClient(object):
    """Interfaces with cloudnode package support for IaaS, intranets, marshalling, track/tracing, and functions"""
    # NOTE: AetherClient supersedes GenericCloudClient and should always be used instead. The basic services
    # of AetherClient are user-login, transaction-tracking, ae:// protocol unpacking, and most of all, the
    # capacity to interchangably switch between AetherClient.request() executing a _local call of the ae://
    # function_ instead of the .request() call bundling a REST API call through the GenericCloudClient interface. The
    # fact that class-scope attributes are global across instances means that these settings can be configured on this
    # object from anywhere in the code, though keep in mind that race-conditions exist as multiple instances are made.

    aether_protocol = "ae://"

    @staticmethod
    def is_ae_endpoint(endpoint): return endpoint.lower().startswith(AetherClient.aether_protocol)

    @staticmethod
    def request(endpoint, d=None, rtype=ReturnType.JSON, method="POST"):
        """This method should be used instead of GenericCloudClient.request()"""

        # the user may use standard REST API endpoints (http:// and https://) or opt use directly call the internal name
        # of the cloudnode and have this request function unpack the endpoint into the http:// or https:// of the
        # request. this has advantage that the cloudnode system can manage the tracking and location of the iaas servers
        # without changing endpoints in the code and user behavior: i.e., ae://function may be deployed by cloudnode to
        # one or more locations and using the ae:// allows the cloudnode to take over management of the URL addresses,
        # which cloudnode already must do, and eventually to allow efficient network distribution. the ae:// request
        # will also do one additional action: it will repackage the j data in a dict wrapper that contains the pid of
        # this thread and a unique tid (transaction id) of the REST API request. This allows independently deployed IAAS
        # to be track-and-trace all the way through the system using only (potentially decentralized) logs information.
        if d is None: d = dict()
        if AetherClient.is_ae_endpoint(endpoint):
            endpoint, wrapped, method = AetherClient.wrap_to_cloudnode_request(endpoint, d)
            r = GenericCloudClient.request(endpoint, d=wrapped, rtype=ReturnType.JSON, method=method)
            if not r.success:
                msg = f"AetherClient request failed: error={r.error}"
                logger.exception(msg)
                r.error = msg
                return r
            uid, pid, tid, data = AetherClient.unwrap_from_cloudnode_kwargs(r.data)
            r.data = GenericCloudClient._marshal_response_text_into_object(data, rtype)
            return r
        else: return GenericCloudClient.request(endpoint, d=d, rtype=rtype, method=method)

    @staticmethod
    def wrap_to_cloudnode_request(endpoint, data):
        ae_name = endpoint[len(AetherClient.aether_protocol):]
        function_name, server_name = ae_name.split(":") if ":" in ae_name else (ae_name, None)
        endpoint = BuildServletConfig.get_endpoint(function_name, servlet_name=server_name)
        tid = uuid.uuid4().hex.lower()[:6]
        pid = "__PID_"  # FIXME
        uid = "__UID_"  # FIXME
        packaged = {"__ae": dict(uid=uid, pid=pid, tid=tid), "d": data}
        logger.info(f"cloudnode aether={endpoint} tid={tid} mapped to {endpoint}")
        return endpoint, packaged, "POST"  # FIX ME, I want this and ReturnType from methods

    @staticmethod
    def is_ae_data(kwargs):
        # NOTE: dict(__ae=<anything1>, d=<anything2>) even though limits could be placed on both values.
        return len(kwargs) == 2 and "__ae" in kwargs.keys() and "d" in kwargs.keys()

    @staticmethod
    def unwrap_from_cloudnode_kwargs(kwargs):
        uid, pid, tid = kwargs["__ae"]["uid"], kwargs["__ae"]["pid"], kwargs["__ae"]["tid"]
        data = kwargs["d"]
        logger.info(f"CloudNode request tid={tid} unpacked.")
        return uid, pid, tid, data

    @staticmethod
    def wrap_to_cloudnode_response(uid, pid, tid, response):
        packaged = {"__ae": dict(uid=uid, pid=pid, tid=tid), "d": response.get_data(as_text=True)}
        return Response(response=json.dumps(packaged), status=response.status)

    @staticmethod
    def unwrap_from_cloudnode_response(response):
        rdata = response.data
        uid, pid, tid, data = rdata["__ae"]["uid"], rdata["__ae"]["pid"], rdata["__ae"]["tid"], rdata["d"]
        logger.info(f"CloudNode response tid={tid} unpacked.")
        return uid, pid, tid, data
