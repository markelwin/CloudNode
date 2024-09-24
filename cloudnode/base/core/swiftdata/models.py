import datetime
import dateparser
import hashlib
import json


class TIMESTAMP(str):
    description = "TIMESTAMP is any string parsable or datetime object; e.g., '2/2/20', isoformat string, .now()"

    @staticmethod
    def upon_disk_storage(value):
        return value.isoformat()

    @staticmethod
    def upon_get(value):
        if value is None: return None
        dt = dateparser.parse(value)
        return dt

    @staticmethod
    def upon_set(value):
        if value is None: return None
        if isinstance(value, datetime.datetime): value = value.isoformat()
        elif isinstance(value, str): value = dateparser.parse(value).isoformat()
        else: raise ValueError("unrecognized format not datetime or str")
        return value


class TEXT(str):
    description = "TEXT can support tokenized searchable language (analyze=true) or exact match i.e., keywords."


class FLAGS(str):
    description = "FLAGS a key<str>-value<str> for exact searchable pipeline states"""

    @staticmethod
    def upon_get(s):
        if s is None: return None
        return json.loads(s)

    @staticmethod
    def upon_set(value):
        if value is None: return None
        if isinstance(value, dict): value = json.dumps(value)
        elif isinstance(value, str): value = json.dumps(json.loads(value))  # poor man verify
        else: raise ValueError("unrecognized format not dict or str")
        return value


class GEOPOINT(str):
    description = "GEOPOINT is a geospatial lat/lng or lat/lng/z in [lat, long], 'lat,lng' or similar formats."""

    @staticmethod
    def upon_get(s):
        if s is None: return None
        return json.loads(s)

    @staticmethod
    def upon_set(value):
        if value is None: return None
        if isinstance(value, str): value = value.split(",")  # "60.503,-40.56"
        if len(value) != 2 and len(value) != 3: raise ValueError(f"geopoint must be length 2 or 3 {value}")
        if isinstance(value, (list, tuple)): value = json.dumps([float(s_or_f) for s_or_f in value])
        else: raise ValueError("unrecognized format not list/tuple or comma separated str of floats")
        return value


class VECTOR(str):
    description = "VECTOR is a vector of floats; e.g., an embedding vector"""

    @staticmethod
    def upon_get(s):
        if s is None: return None
        return json.loads(s)

    @staticmethod
    def upon_set(value):
        if value is None: return None
        if isinstance(value, (list, tuple)): value = json.dumps([float(s_or_f) for s_or_f in value])
        else: raise ValueError("unrecognized format not list/tuple or comma separated str of floats")
        return value


class INTEGER(str):
    description = "INTEGER is an integer."""

    @staticmethod
    def upon_get(s):
        if s is None: return None
        return json.loads(s)

    @staticmethod
    def upon_set(value):
        if value is None: return None
        return json.dumps(value)


class FLOAT(INTEGER):
    description = "FLOAT is an double-precision float."""


class BOOLEAN(INTEGER):
    description = "BOOLEAN is an True/False states as such."""


def derived_field(swift_cls, es_field_cls_name, **parameters):
    md5 = hashlib.md5(json.dumps(parameters).encode()).hexdigest()
    derived = type(f"{swift_cls.__name__}_{md5}", (swift_cls,), {})
    derived.__es_parameters = parameters
    derived.__es_field_cls_name = es_field_cls_name
    return derived


def GENERIC_STRING(list=False, analyze=False, dont_index=False):
    if analyze: return derived_field(TEXT, "Text", multi=list, dont_index=dont_index)
    else: return derived_field(TEXT, "Keyword", multi=list, dont_index=dont_index)


def GENERIC_TIMESTAMP(list=False, dont_index=False):
    return derived_field(TIMESTAMP, "Date", is_list=list, dont_index=dont_index)


def GENERIC_FLAGS(dont_index=False):
    return derived_field(FLAGS, "Keyword", dont_index=dont_index)


def GENERIC_GEOPOINT(list=False, dont_index=False):
    return derived_field(GEOPOINT, "GeoPoint", is_list=list, dont_index=dont_index)


def GENERIC_VECTOR(n_dims, dont_index=False):
    return derived_field(VECTOR, "DenseVector", n_dims=n_dims, dont_index=dont_index)

def GENERIC_INTEGER(list=False, dont_index=False):
    return derived_field(INTEGER, "Integer", is_list=list, dont_index=dont_index)


def GENERIC_FLOAT(list=False, dont_index=False):
    return derived_field(FLOAT, "Float", is_list=list, dont_index=dont_index)


def GENERIC_BOOLEAN(list=False, dont_index=False):
    return derived_field(BOOLEAN, "Boolean", is_list=list, dont_index=dont_index)


class sd(object):
    string = GENERIC_STRING
    timestamp = GENERIC_TIMESTAMP
    flags = GENERIC_FLAGS
    geopoint = GENERIC_GEOPOINT
    vector = GENERIC_VECTOR
    integer = GENERIC_INTEGER
    float = GENERIC_FLOAT
    boolean = GENERIC_BOOLEAN


descriptions_of_sd = {
    GENERIC_STRING: TEXT,
    GENERIC_TIMESTAMP: TIMESTAMP,
    GENERIC_FLAGS: FLAGS,
    GENERIC_GEOPOINT: GEOPOINT,
    GENERIC_VECTOR: VECTOR,
    GENERIC_INTEGER: INTEGER,
    GENERIC_FLOAT: FLOAT,
    GENERIC_BOOLEAN: BOOLEAN,
}
