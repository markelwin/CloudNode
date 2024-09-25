from cloudnode.base.core.lightweight_utilities.sysops import dynamic_variable_loader
from cloudnode.base.core.lightweight_utilities.misc_logging import LogEveryS
from cloudnode.base.iaas.for_functions import parse_function_config_into_source
from cloudnode.base.iaas.nodes.BuildServletConfig import BuildServletConfig
from cloudnode.base.iaas.nodes.TraditionalCloudFunction import TraditionalCloudFunction
from cloudnode.base.iaas.cron import EasyCron
from flask_cors import CORS
import threading
import flask
import inspect
import datetime
import time

from cloudnode.base.core.lightweight_utilities.profiler_logger import ProfilerLogger
profiler, logger = ProfilerLogger.getLogger(__name__)

# Infrastructure is the core of app building, consisting of a server hosting one or more servlets, which are collections
# of node function endpoints at a specific hostport running in its own background daemon thread. Infrastructure bundles
# this server of servlets in a dockerized deployment for placement onto hosts with other co-located apps (build from the
# same or different cloudnode functions) and cloudnode services (such as elasticsearch). This reduces the sysops of the
# entire infrastructure to the serializable servlet configurations and access to their retrievable codebase (such as by
# git checkout of the app repositories); the future standard can therefore deploy any cloudnode app simply with only its
# serialized configuration information and the cloudnode package, with standardized structures and its dependencies.

# Infrastructure is a server built on Flask which performs a blocking start after converting known lists of functions
# into servlets of easyapi endpoints; for convenience, system-level tools such as cron scheduling is also available.

daemon_functions = [
    dict(source="cloudnode.base.iaas.nodes.Infrastructure:Infrastructure.end", as_type="HTTP")
]
daemon_hostport = "0.0.0.0:4137"


class BuildServlet:

    def __init__(self):
        self.config = None
        self.node_builders = []  # NodeBuilders construct APIs (Flask endpoints) from their Python equivalents
        self.thread = None       # The thread that manages the actual background process its Flask functions runs on

        self.flask_app = flask.Flask(__name__)  # The named Flask app to launch the .run() for this servlet. Running one
        CORS(self.flask_app)                    # Flask app for each servlet is not the intended use of Flask so beware.

    @staticmethod
    def build(config):
        logger.info(f"Building servlet protocol={config.protocol} hostpost={config.hostport}")

        # unpack BuildNodeFunctions function_configs from config
        with profiler.profile(f"BUILD_NODE_FUNCTIONS"):
            items_unpacked = []
            for item in config.function_configs:
                module, cls_name, item_method, source_filename = parse_function_config_into_source(item)
                with profiler.profile(f"UNPACK_NODE_FUNCTIONS_{item['source'].upper()}"):
                    # dynamically load the function; if function_name is None then load all methods of cls as functions
                    logger.info(f"Dynamically loading node function(s) defined by: {item}")
                    cls = dynamic_variable_loader(module, cls_name)
                    if item_method is not None: methods = [item_method]
                    else: methods = [name for name, _ in inspect.getmembers(cls, predicate=inspect.isfunction)
                                     if not name.startswith("_")]
                    # check whether the cls has args (apply to all) and args_for (apply by name)
                    args_default = getattr(cls, "args") if hasattr(cls, "args") else dict()
                    args_by_method = getattr(cls, "args_for") if hasattr(cls, "args_for") else dict()
                    logger.info(f"BuildServlet unpacked source={item['source']} into functions={methods}")
                    for method in methods:
                        source = f"{module}:{cls_name}.{method}"
                        args = args_default | (args_by_method[method] if method in args_by_method else dict()) | dict(source=source)
                        # handle special use cases e.g., HTTP and NODE. To be standardized as the protocols standardize.
                        if "as_type" in args and args["as_type"] == "HTTP": args = args | dict(do_json=False, methods=["GET"])
                        items_unpacked.append(args)

            # create the unpacked config, write itself to disk, create the builders; base_sysop already included above
            unpacked = BuildServletConfig(protocol=config.protocol, hostport=config.hostport, servlet_name=config.servlet_name,
                                          no_base_sysops=True).add_functions(items_unpacked).integrity_confirmed(unpacked=True).to_disk_configs_by_servlet()

            builder = BuildServlet()
            builder.config = unpacked
            for item in unpacked.function_configs:
                builder.node_builders.append(TraditionalCloudFunction(unpacked.servlet_name, item))
        return builder

    def start(self):
        """starts a background thread containing the flask.run() for its hostport; i.e., starts to run this servlet"""
        # NOTE: daemon=True ensures that all servlets are automatically ended when the main program Infrastructure ends
        if self.config is None: raise RuntimeError("BuildServlet.build() must be run before BuildServlet.start()")
        protocol, hostport, servlet_name = self.config.protocol, self.config.hostport, self.config.servlet_name
        logger.info(f"Starting servlet={servlet_name} protocol={protocol} hostpost={hostport}")
        for b in self.node_builders: b.flask_route(self.flask_app)
        (host, port), uid = hostport.split(":"),  f"{protocol}{hostport}"
        if uid in Infrastructure.servlets: raise RuntimeError(f"servlet {uid} already running: {Infrastructure.servlets.keys()}")
        self.thread = threading.Thread(target=self.flask_app.run, args=(host, int(port)), name=f"servlet={uid}", daemon=True)
        self.thread.start()

        endpoints = {b.name: f"{protocol}{hostport}{b.route}" for b in self.node_builders}
        BuildServletConfig.endpoints_by_function_to_disk(endpoints, self.config.servlet_name)

    def end(self):
        if self.config is None: raise RuntimeError("BuildServlet.start() must be run before BuildServlet.end()")
        protocol, hostport, servlet_name = self.config.protocol, self.config.hostport, self.config.servlet_name
        logger.info(f"Ending servlet={servlet_name} protocol={protocol} hostport={hostport}")


class Infrastructure(object):

    admin = None
    abort_now = False
    servlets = dict()
    flask_app = None
    crons = []

    @staticmethod
    def set_admin(oauth2): Infrastructure.admin = oauth2

    @staticmethod
    def clear():
        # Clear the endpoints known by the system: note: this should move inside BuildServletConfig eventually.
        Infrastructure.admin = None
        Infrastructure.abort_now = False
        Infrastructure.servlets = dict()
        Infrastructure.flask_app = None
        Infrastructure.crons = []
        BuildServletConfig.empty_disk()
        return Infrastructure

    @staticmethod
    def servlet(hostport, functions, servlet_name=None, no_base_sysops=False):
        logger.info(f"Infrastructure BuildServlet hostport={hostport} functions={functions}")
        config = BuildServletConfig(hostport=hostport, servlet_name=servlet_name, no_base_sysops=no_base_sysops)\
            .add_functions(functions).integrity_confirmed()
        servlet = BuildServlet.build(config)  # servlet has an updated config
        Infrastructure.servlets[config.servlet_name] = servlet
        return servlet

    @staticmethod
    def thirdparty(hostport, servlet, servlet_name=None):
        logger.info(f"Infrastructure adding thirdparty app={servlet.provider} hostport={hostport}")
        if servlet_name is None: servlet_name = hostport
        Infrastructure.servlets[servlet_name] = servlet(hostport)
        return servlet

    @staticmethod
    def add_crons(to_add): [Infrastructure.crons.append(EasyCron(**cron)) for cron in to_add]

    @staticmethod
    def blocking_start():
        logger.info(f"Adding daemon servlet functions on hostport={daemon_hostport}")
        Infrastructure.servlet(daemon_hostport, daemon_functions)
        for servlet in Infrastructure.servlets.values(): servlet.start()

        _every = LogEveryS(logger, n_sec=60, and_first=True)
        while True:
            _every.log("INFO", f"Infrastructure server still running: current time={datetime.datetime.now().isoformat()}")
            time.sleep(0.2)
            if Infrastructure.abort_now:
                logger.info("Infrastructure abort_now=True command received. Initiated shutdown.")
                exit()  # this is a correct solution when all servers are daemons (c.f. their thread config)
            for cron in Infrastructure.crons: cron.do_if_time_has_lapsed()

    @staticmethod
    def end():
        Infrastructure.abort_now = True
        return f"SHUTDOWN INITIATED at={datetime.datetime.now().isoformat()}"
