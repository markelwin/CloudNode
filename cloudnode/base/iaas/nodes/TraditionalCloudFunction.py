from cloudnode.base.iaas.for_functions import parse_function_config_into_source
from cloudnode.base.iaas.CloudNodeLogger import CloudNodeLogger
from cloudnode.base.core.lightweight_utilities.dicts import dictionary_parser
from cloudnode.base.core.lightweight_utilities.sysops import dynamic_variable_loader
from http import HTTPStatus
import datetime
import json


from cloudnode.base.core.lightweight_utilities.profiler_logger import ProfilerLogger
profiler, logger = ProfilerLogger.getLogger(__name__)

# authentication: relatively simple; password, whitelist, blacklist, firebase (until replaced). low priority v1.weeks
# nodelogger: this needs to inspect into code by default and should be included in v1.2
# conda testing and deployment: would validate credibility of code very highly v.1.0 or v1.weeks.
# function requirements: too complicated for home server v.1.improvements
# iam: v.1.infrastructure.2
# do_json ==> because we want to support an HTTP server as well
# infrastructure => host number of nodes (i.e., that is all); and traditionalfunction exists only as heritage re cloud
# configs in class <== staticmethod <== written to yaml at launch of Infrastructure class
# except want user to be able to simply decorate a function?
# traditional functions <== streaming (i.e., data in request) v. stub? (crucial for graphs)
# should infrastructure handle that?
# rewrite DynamicSingletonImporter as a property .content
# since cloud storage is now; add to logs (in a single json instance) and its profiling too
# remember to add 'hardware we use' in the readme

# TraditionalCloudFunction is intended to maintain a basic standard of engineering which allows its function_config to
# be sufficient to generate a CloudFunction which can be uploaded to various CloudFunction hosting services i.e. Google.


class TraditionalCloudFunction:

    default_methods = ["POST"]
    default_timeout_s = 540
    default_do_json = True

    route_format = "/functions/{name}"

    def __init__(self, servlet_name, function_config):

        module, cls_name, function_method, source_filename = parse_function_config_into_source(function_config)
        if function_method is None: raise ValueError("item_method must not be None")
        name = f"{cls_name}.{function_method}"

        # NOTE: source is path.to.file:function if function is in file.py; without : means function name == file name
        self.name = name
        self.servlet_name = servlet_name
        self.depends_on = dictionary_parser(function_config, "depends_on", not_found_value=[])
        self.module = module
        self.source_filename = source_filename
        self.function = None
        self.function_config = function_config

        # basic configuration of cloud function deployment
        self.timeout_s = dictionary_parser(function_config, "timeout_s", not_found_value=self.default_timeout_s)
        self.do_json = dictionary_parser(function_config, "do_json", not_found_value=self.default_do_json)

        # configuration of endpoints and their expectations
        self.route = self.route_format.format(name=self.name)
        self.methods = dictionary_parser(function_config, "methods", not_found_value=self.default_methods)

    def flask_route(self, app):
        """Creates Flask ingress to access Python function. Flask expects no arguments; instead retrieved by request"""
        logger.info(f"add TraditionalCloudFunction to Flask name={self.name} methods={self.methods} route={self.route}")
        flask_ingress = self.__python_function_as_flask_ingress()
        def flask_accepts_no_arguments_wrapper():
            from flask import request
            return flask_ingress(request)
        flask_accepts_no_arguments_wrapper.__name__ = self.name
        app.add_url_rule(self.route, view_func=flask_accepts_no_arguments_wrapper, methods=self.methods)


    ###################################################################################################################
    # NOTE: Code below this line is for wrapping of Python functions to create IaaS endpoints and their profiling.
    ###################################################################################################################

    def __python_function_as_flask_ingress(self):
        """This function constructs all Flask requirements for executing the Python function self.function"""
        # NOTE: This wraps self.function to accept its arguments from the request and packages outbound results as a
        # response. This method first imports any remaining modules necessary to load the original self.function
        # representation; then defines a more formal Flask ingress: server_entrypoint_suitable_for_profiling_and_logging
        # which exists to encapsulate any server features, such as iam (not yet included), authentication of the request
        # (not yet included), initiation of profiling (to record function performance) and cloud logging (for storage of
        # the logs in a unified database across servers), and so forth; it is this function that "transforms" the Python
        # function to a server inbound execution api. This function also looks into the request for one of a few simple
        # meta requests asking to  report on any number of characteristics of any cloud function (ping, metadata, etc).
        from flask import Response
        if self.function is None:
            class_name, function_name = self.name.split(".") if "." in self.name else (None, self.name)
            if class_name is None:
                self.function = dynamic_variable_loader(self.module, function_name)
            else: self.function = getattr(dynamic_variable_loader(self.module, class_name), function_name)
        if self.function is None:
            raise RuntimeError(f"Configuration error: {self.name} is unable to resolve function.")

        # NOTE: This block of code handles special flags (e.g. __ping) for the Python function.
        def available_meta_operations_and_python_function(kwargs):
            try:
                # expectation: kwargs=dict(__is_awake=<any_value>)
                # __is_awake is to ensure functions do not shut down, with minimum egress cost.
                # __ping returns local time to measure round trip latency.
                # __metadata is currently only name to solve a problem of identifying functions-frameworks urls,
                # Remember that egress cost is expensive on most commercial cloud provider systems.
                if len(kwargs) == 1 and "__is_awake" in kwargs.keys():
                    logger.info("Received IS_AWAKE request: returning confirmation with True response.")
                    return Response(response=json.dumps(True))
                if len(kwargs) == 1 and "__ping" in kwargs.keys():
                    utc_now = datetime.datetime.now().astimezone(datetime.timezone.utc).replace(tzinfo=None).isoformat()
                    logger.info(f"Received PING request: returning current system utc_now={utc_now}.")
                    return Response(response=json.dumps(dict(utc_now=utc_now)))
                if len(kwargs) == 1 and "__metadata" in kwargs.keys():
                    metadata = dict(name=self.name)
                    logger.info(f"Received METADATA request: returning {metadata}.")
                    return Response(response=json.dumps(metadata))
                # Continue onward into the normal operating Cloud Function calls.
                args_s = {k: f"{str(v)[:5000]}" for k, v in kwargs.items()}
                logger.info(f"entering Function {self.name}: {args_s}")
                results = self.function(**kwargs)
                if self.do_json: results = json.dumps(results)
                return Response(response=results)
            except Exception as e:
                msg = f"{type(e)}: {e}"
                status = e.args[1] if len(e.args) > 1 else HTTPStatus.INTERNAL_SERVER_ERROR
                logger.error(f"{status}: {msg}")
                return Response(response=msg, status=status)

        def server_entrypoint_suitable_for_profiling_and_logging(request):
            with CloudNodeLogger() as logger:  # switch to CloudNodeLogger from base local logger
                # s = profiler.swift(f"NODE_{self.name.upper()}").add(bytes=sd.integer()).as_rates()
                with profiler.profile(f"NODE_{self.name.upper()}") as p:
                    # parsing request into function arguments
                    if request.method == "GET": kwargs = dict(request.args)
                    elif request.method == "POST": kwargs = request.get_json()
                    else: raise NotImplemented(f"Request method {request.method} unknown, must be GET or POST.")
                    # checking whether the request is for one of the meta instructions instead
                    response = available_meta_operations_and_python_function(kwargs)
                    p.add(dict(bytes=response.content_length))
                    # FIXME: do the change to upload the logs and return with the errors stub.
                    return response
        return server_entrypoint_suitable_for_profiling_and_logging

# FIXME: profiler.swift().add(bytes=sd.integer()).as_rates() <== add name automatically;