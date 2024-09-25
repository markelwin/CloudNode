from cloudnode.base.core.lightweight_utilities.filesystem import FileSystem
from cloudnode.base.iaas.for_functions import base_functions, parse_function_config_into_source
from cloudnode import RuntimeConfig
import random
import json
import os
import io

nf_filename_configs = "file://" + os.path.join(RuntimeConfig.directory_base_local, "_subsystem/infrastructure/nf_configs_by_servlet.json")
nf_filename_endpoints = "file://" + os.path.join(RuntimeConfig.directory_base_local, "_subsystem/infrastructure/nf_endpoints_by_function.json")


class BuildServletConfig(object):

    def __init__(self, hostport, protocol="http://", servlet_name=None, no_base_sysops=True):
        self.servlet_name = hostport if servlet_name is None else servlet_name
        self.hostport = hostport
        self.protocol = protocol
        self.function_configs = []  # simply a list of function configs as dictionaries
        if not no_base_sysops: self.add_functions(base_functions)  # adds cloudnode base sysops functions

    def add_functions(self, to_include):
        if not isinstance(to_include, (list, tuple)): to_include = [to_include]
        self.function_configs.extend(to_include)
        return self

    def integrity_confirmed(self, unpacked=False):
        """runs any number of integrity checks on the current servlet config; throws an error if any config failures"""
        BuildServletConfigIntegrityChecks.confirm_functions_pass_integrity_checks(self, unpacked=unpacked)
        return self

    @staticmethod
    def get_function_name_from_function_config(function_config, unpacked):
        _, cls_name, method_name, _ = parse_function_config_into_source(function_config)
        if unpacked and method_name is None: raise RuntimeError("BuildServletConfig not properly unpacked with .build()")
        return cls_name if method_name is None else f"{cls_name}.{method_name}"

    @staticmethod
    def empty_disk():
        if os.path.exists(nf_filename_configs): FileSystem.easy_delete(nf_filename_configs)
        if os.path.exists(nf_filename_endpoints): FileSystem.easy_delete(nf_filename_endpoints)

    def to_disk_configs_by_servlet(self):
        # NOTE: see note in endpoints_to_disk to understand the format of cf_configurations_filename
        if FileSystem.easy_exists(nf_filename_configs):
            configs_by_servlet = json.load(FileSystem.easy_download(nf_filename_configs))
        else: configs_by_servlet = dict()

        function_configs = dict()
        for item in self.function_configs:
            function_name = self.get_function_name_from_function_config(item, unpacked=True)
            if function_name in function_configs: raise RuntimeError(f"BuildServletConfig contains duplicates items={self.function_configs}")
            function_configs[function_name] = item
        configs_by_servlet[self.servlet_name] = dict(functions=function_configs,
                                                     metadata=dict(hostport=self.hostport, protocol=self.protocol))
        FileSystem.easy_upload(io.StringIO(json.dumps(configs_by_servlet, indent=2)), nf_filename_configs)
        return self

    @staticmethod
    def from_disk_configs_by_servlet(servlet_name):  # FIXME: note; everything necessary to rebuild a servlet from scratch
        if os.path.exists(nf_filename_configs):
            configs_by_servlet = json.load(FileSystem.easy_download(nf_filename_configs))
        else: raise RuntimeError(f"configs_by_servlet file does not exist stub={nf_filename_configs}")
        if servlet_name not in configs_by_servlet:
            raise RuntimeError(f"servlet={servlet_name} not found in configs_by_servlet={configs_by_servlet.keys()}")
        try: metadata, function_configs = configs_by_servlet[servlet_name]["metadata"], configs_by_servlet[servlet_name]["functions"]
        except: raise ValueError(f"servlet={servlet_name} configs_by_servlet not properly formed data={configs_by_servlet[servlet_name]}")
        return BuildServletConfig(servlet_name=servlet_name, **metadata, no_base_sysops=True)\
            .add_functions(function_configs.values()).integrity_confirmed()

    @staticmethod
    def endpoints_by_function_to_disk(endpoints_by_function_name, servlet_name):
        # NOTE: endpoints_by_function_to_disk is a dict(function_name=<URL>) global lookup table of all servers running
        # across hosts, so that Infrastructure clients can specify a servlet_name (usually the hostport) and function
        # and find its API url. This allows expansion into multiple hosts and client ease i.e., ae://function:server
        if FileSystem.easy_exists(nf_filename_endpoints):
            endpoints = json.load(FileSystem.easy_download(nf_filename_endpoints))
        else: endpoints = dict()
        for function_name, endpoint in endpoints_by_function_name.items():
            if function_name not in endpoints: endpoints[function_name] = dict()
            if servlet_name not in endpoints[function_name]: endpoints[function_name][servlet_name] = []
            endpoints[function_name][servlet_name].append(endpoint)
        FileSystem.easy_upload(io.StringIO(json.dumps(endpoints, indent=2)), nf_filename_endpoints)

    @staticmethod
    def get_endpoint(function_name, servlet_name=None):
        # NOTE: see note in endpoints_to_disk; if servlet_name is None, a random servlet is selected
        if not FileSystem.easy_exists(nf_filename_endpoints):
            raise RuntimeError(f"endpoints stub={nf_filename_endpoints} does not exist: server build malfunction?")
        endpoints_by_function = json.load(FileSystem.easy_download(nf_filename_endpoints))
        if function_name not in endpoints_by_function:
            raise KeyError(f"endpoint for function={function_name} not found among function={endpoints_by_function.keys()}")
        endpoints = endpoints_by_function[function_name]
        if servlet_name is not None:
            if servlet_name not in endpoints:
                raise KeyError(f"servlet={servlet_name} function={function_name} not found among servlets={endpoints.keys()}")
            choices = endpoints[servlet_name]
        else: choices = random.choice(list(endpoints.values()))
        return random.choice(choices)  # select one of the random endpoints associated with that servlet_name


class BuildServletConfigIntegrityChecks:

    @staticmethod
    def confirm_functions_pass_integrity_checks(config, unpacked=False):
        """This routine checks that all Node Function dependencies are included on the same Servlet."""
        function_names = [config.get_function_name_from_function_config(item, unpacked) for item in config.function_configs]
        duplicates = {x for x in function_names if function_names.count(x) > 1}
        if len(duplicates) > 0: raise RuntimeError(f"Duplicate function names found at load-time: {duplicates}")
        is_missing = []
        for i, item in enumerate(config.function_configs):
            if "depends_on" not in item: continue
            for depends_on in item["depends_on"]:
                if depends_on not in function_names:
                    is_missing.append(f"{function_names[i]} needs {depends_on}")
        if len(is_missing) > 0: raise RuntimeError(f"These dependencies are missing: {is_missing}")
