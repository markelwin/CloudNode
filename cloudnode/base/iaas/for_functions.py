

# Default node functions available to all servlets
base_functions = [
    dict(source="cloudnode.functions.admin:NFSysops.system_healthcheck", methods=["GET"]),
]


def parse_function_config_into_source(item):
    """Transforms module:class.method and when method is not included all methods of class will be loaded"""
    module, cls_name = item["source"].split(":")
    cls_name, method_name = cls_name.split(".") if "." in cls_name else (cls_name, None)
    source_filename = module.replace(".", "/") + ".py"
    return module, cls_name, method_name, source_filename
