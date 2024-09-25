from cloudnode.base.core.elasticsearch.search import ElasticSearchDslClient, ElasticSearchServer, ElasticSearchClient
from cloudnode.base.core.lightweight_utilities.filesystem import FileSystem
from cloudnode.base.core.lightweight_utilities.cloudnode import create_programmatic_directory
from cloudnode.base.core.swiftdata.models import sd, descriptions_of_sd
from cloudnode.config import RuntimeConfig
from elasticsearch_dsl import Document, Integer, Keyword, Text, Date, Index, Float, Boolean, GeoPoint, DenseVector, Q
import dataclasses
import datetime
import json
import uuid
import os
import io
import re

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SwiftData creates database functionality with simplicity by extending Python dataclass and type-mapping to
# ElasticSearch (for persistence and larger-scale search), also enabling data to be written to local filesystems.

# The intention here is to provide end-to-end data creation on device applications to storage and search with one-size-
# fits-all data APIs, or creation of search engine scale applications with the startup simplicity of Python dataclasses.
# Each SwiftData instance is subclassed from the SwiftData class, which also contains mandatory .id and .ts fields so
# that each datum is uniquely identifiable and has an assigned creation timestamp.

# The SwiftData is the canonical working format of the data withing CloudNode, i.e., data is transfer to ElasticSearch
# Document objects at points of data writing to ElasticSearch; and transformed back from ElasticSearch after queries.
# This is memory and performance efficient because ESD are simply containers for json rest api calls in the es format.


@dataclasses.dataclass
class SwiftData:
    id: sd.string()
    ts: sd.string()
    # ts: sd.timestamp()

    def __init_subclass__(cls):
        """This method is called after any SubClass /definition/ and servers the purpose of set/get of its fields."""
        # NOTE: there are instances in which fields (i.e., timestamps) should have data wranglers when set or get (i.e.
        # the user may set the timestamp field with a string instead of a datetime; which is then parsed in the setter
        # of the field according to the timestamp.upon_set(value) function, if defined; similarly for getters. This lets
        # dataclass use conventional styles (strings) for storage on object by allows the user to have the full suite of
        # expectations (i.e., gps = "lat,lng" or ["lat", "lng"] or [lat, lng]) all while seamlessly connecting from the
        # dataclass to its json to its elasticsearch document (where json has its wrangler into elasticsearch too)
        super().__init_subclass__()
        for field in dataclasses.fields(cls):
            if hasattr(field.type, "upon_get") or hasattr(field.type, "upon_set"):
                private = f"__{field.name}"
                # cls.__annotations__[private] = str  # this backup confirms all private holdings are str
                setattr(cls, private, dataclasses.field(init=False, repr=False))
                if hasattr(field.type, "upon_get"):
                    getter = property(lambda self: field.type.upon_get(getattr(cls, private)))
                else: getter = property(lambda self: getattr(cls, private))
                if hasattr(field.type, "upon_set"):
                    setter = getter.setter(lambda self, value: setattr(cls, private, field.type.upon_set(value)))
                else: setter = getter.setter(lambda self, value: setattr(cls, private, value))
                setattr(cls, field.name, getter)
                setattr(cls, field.name, setter)

    @classmethod
    def empty(cls):
        """Initializer that populates all fields with empty objects. Useful for updating or merging records."""
        return cls(**{field.name: None for field in dataclasses.fields(cls)})

    @classmethod
    def new(cls, id=None, ts=None, **data):
        """Initializer that accepts missing values (set to empty); and sets .id and .ts if not provided."""
        if data is None: data = dict()
        values = {f.name: data[f.name] if f.name in data else None for f in dataclasses.fields(cls)}
        if id is None and "id" not in data: values["id"] = uuid.uuid4().hex.lower()
        if id is not None: values["id"] = str(id).lower()  # if id or ts are set these values will override any in data
        if ts is None and "ts" not in data: values["ts"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if ts is not None: values["ts"] = ts
        # because constructors do not call setters unless explicit within the init we will explicitly use setters
        for field in dataclasses.fields(cls):
            if hasattr(field.type, "upon_set") and field.name in values:
                values[field.name] = field.type.upon_set(values[field.name])
                if hasattr(field.type, "upon_get") and field.name in values:
                    values[field.name] = field.type.upon_get(values[field.name])
        return cls(**values)

    def as_dict(self):
        return dataclasses.asdict(self)

    # The methods below this line will be modified once the ElasticSearch components are handled.

    def save(self, index, exist_ok=True, es=False):
        if es:
            es_client, es_cls = SwiftDataBackend.operation_context(index, self.__class__)
            return es_cls(**SwiftDataInternal.swiftdata_obj_es_init(self)).save(using=es_client)
        else:
            stub = SwiftDataBackend.create_stub(self.id, self.__class__.__name__, index)
            if not exist_ok and FileSystem.easy_exists(stub):
                raise RuntimeError(f"item exists in database {self}")
            as_dict = self.as_dict()
            for field in dataclasses.fields(self.__class__):
                if hasattr(field.type, "upon_disk_storage") and field.name in as_dict:
                    as_dict[field.name] = field.type.upon_disk_storage(as_dict[field.name])
            FileSystem.easy_upload(io.StringIO(json.dumps(as_dict)), stub)
        return "created"  # follows the ElasticSearch response convention.

    @classmethod
    def delete(cls, index, id, es=False):
        if es:
            es_client, es_cls = SwiftDataBackend.operation_context(index, cls)
            return cls.get(index, id, es=True).delete(using=es_client)  # there is some strange oddity here
            # return es_cls(**SwiftDataInternal.swiftdata_obj_es_init(cls.new(id=id))).delete(using=es_client)
        else:
            stub = SwiftDataBackend.create_stub(id, cls.__name__, index)
            return FileSystem.easy_delete(stub)

    @classmethod
    def get(cls, index, id, es=False):
        if es:
            es_client, es_cls = SwiftDataBackend.operation_context(index, cls)
            if isinstance(id, (tuple, list)):
                return es_cls.mget(id=id, using=es_client)
            else: return es_cls.get(id=id, using=es_client)
        else:
            if not isinstance(id, (tuple, list)): id = [id]
            objects = []
            for _id in id:
                if not cls.exists(index, _id): result = None
                else:
                    stub = SwiftDataBackend.create_stub(id, cls.__name__, index)
                    file_obj = FileSystem.easy_download(stub)
                    result = cls.new(json.load(file_obj))
                objects.append(result)
            return objects

    @classmethod
    def getAll(cls, index, es=False, max_results=50):
        if es:
            es_client, es_cls = SwiftDataBackend.operation_context(index, cls)
            es_objs = ElasticSearchDslClient.getAll(es_client, es_cls, max_results=max_results)
            return [cls(**SwiftDataInternal.es_obj_swiftdata_init(obj)) for obj in es_objs]
        else:
            objs = []
            for id in cls.list(index)[:max_results]:
                stub = SwiftDataBackend.create_stub(id, cls.__name__, index)
                file_obj = FileSystem.easy_download(stub)
                objs.append(cls.new(**json.load(file_obj)))
            return objs

    @classmethod
    def exists(cls, index, id, es=False):
        if es:
            es_client, es_cls = SwiftDataBackend.operation_context(index, cls)
            return es_cls.exists(id=id, using=es_client)
        else:
            stub = SwiftDataBackend.create_stub(id, cls.__name__, index)
            return FileSystem.easy_exists(stub)

    @classmethod
    def list(cls, index, es=False):
        if es:
            es_client, es_cls, es_index = SwiftDataBackend.operation_context(index, cls, with_index=True)
            return ElasticSearchDslClient.listAll(es_client, es_index._name, es_cls)
        else:
            directory = SwiftDataBackend.create_stub(None, cls.__name__, index)
            filenames = FileSystem.easy_listdir(directory)
            pattern = re.compile(f"swift.{index}.{cls.__name__}.(.*?).json".lower())
            return [pattern.match(filename).group(1) for filename in filenames if pattern.match(filename)]

    @classmethod
    def refresh_index(cls, index, es=False):
        if es:
            es_client, es_cls, es_index = SwiftDataBackend.operation_context(index, cls, with_index=True)
            es_client.indices.refresh(index=es_index._name)

    @classmethod
    def count(cls, index, es=False):
        if es:
            _, es_cls, es_index = SwiftDataBackend.operation_context(index, cls, with_index=True)
            return SwiftDataBackend.client.count(es_index._name)
        else:
            return len(cls.list(index))

    @classmethod
    def create_index(cls, index, exist_ok=False):
        """makes explicit for the user the creation of the elastic search document index for the first time"""
        es_client, es_cls, es_index = SwiftDataBackend.operation_context(index, cls, with_index=True)
        if not SwiftDataBackend.client.index_exists(es_index._name):
            logger.info(f"creating index {es_index._name} for {es_cls.__name__} for its first use")
            es_index.create(using=SwiftDataBackend.client.es)
        else:
            if exist_ok: return
            raise RuntimeError(f"index {es_index._name} for {es_cls.__name__} already exists")

    @classmethod
    def expert_query(cls, index, q, max_results=50):
        """performs a search using any elasticsearch-dsl Q query construction"""
        es_client, es_cls = SwiftDataBackend.operation_context(index, cls)
        es_objs = ElasticSearchDslClient.perform_dsl_query(es_client, es_cls, q, max_results=max_results)
        return [cls(**SwiftDataInternal.es_obj_swiftdata_init(obj)) for obj in es_objs]

    @classmethod
    def search_bar(cls, index, s, max_results=50):
        """performs a search bar like query on a string with field prompts, i.e., "cast: david year: 1980" """
        return cls.expert_query(index, ElasticSearchDslClient.search_bar(s), max_results=max_results)

    @classmethod
    def search_any(cls, index, s, fields=None, max_results=50):
        """performs a search such that s may be in any of fields; or all text fields if not set by user."""
        # NOTE: OR is spelled should; AND is spelled must; NOR is spelled must_not; ignore score must is filter
        # NOTE: https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-bool-query.html
        # NOTE: https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-multi-match-query.html
        if fields is None: fields = [f.name for f in dataclasses.fields(cls) if f.type.__name__.split("_")[0] == "TEXT" and f.name not in ["id", "ts"]]
        q = Q('multi_match', **dict(query=s, fields=fields))
        return cls.expert_query(index, q, max_results=max_results)

    @staticmethod
    def help():
        """provides help to the user provided the existing use case"""
        logger.info("SwiftData (tm) supports numerous datatypes:")
        for name, function in sd.__dict__.items():
            if name.startswith("__"): continue
            if function not in descriptions_of_sd: continue

            default = descriptions_of_sd[function]
            description = default.description if hasattr(default, "description") else "no description provided"
            logging.info(f"{name:>15s}: {description}")


class SwiftDataBackend(object):

    server = None
    client = None
    swiftdata_base_directory = "file://" + os.path.join(RuntimeConfig.directory_base_local, "_subsystem/swiftdata/")

    def start(self, password, exist_ok=False, rebuild=False):
        if not exist_ok and (SwiftDataBackend.server is not None or SwiftDataBackend.client is not None):
            raise RuntimeError("SwiftDataBackend has previously been started and is not intended for parallelization.")
        if rebuild: ElasticSearchServer.force_delete()
        SwiftDataBackend.server = ElasticSearchServer(password=password, exist_ok=exist_ok, run_ok=exist_ok)
        SwiftDataBackend.client = ElasticSearchClient(password=password)
        SwiftDataBackend.client.wait_for_active()
        return self

    def stop(self, not_exist_ok=False): ElasticSearchServer.stop(not_exist_ok=not_exist_ok)

    def snapshot_save(self, applet):
        self.__throwing_integrity_check()
        directory = os.path.join(SwiftDataBackend.swiftdata_base_directory, "_snapshots/elasticsearch/_applet", applet)[len("file://"):]
        self.client.snapshot_directory_set(directory, applet)
        return self.client.snapshot_save(applet)

    def snapshot_load(self, applet, save_name):
        self.__throwing_integrity_check()
        directory = os.path.join(SwiftDataBackend.swiftdata_base_directory, "_snapshots/elasticsearch/_applet", applet)[len("file://"):]
        self.client.snapshot_directory_set(directory, applet)
        return self.client.snapshot_load(applet, save_name)

    def snapshot_latest(self, applet):
        self.__throwing_integrity_check()
        directory = os.path.join(SwiftDataBackend.swiftdata_base_directory, "_snapshots/elasticsearch/_applet", applet)[len("file://"):]
        self.client.snapshot_directory_set(directory, applet)
        return self.client.snapshot_latest(applet)

    def snapshot_list(self, applet, n_most_recent=10):
        self.__throwing_integrity_check()
        directory = os.path.join(SwiftDataBackend.swiftdata_base_directory, "_snapshots/elasticsearch/_applet", applet)[len("file://"):]
        self.client.snapshot_directory_set(directory, applet)
        return self.client.snapshot_list(applet, n_most_recent=n_most_recent)

    @staticmethod
    def operation_context(index, cls, with_index=False):
        """Convenience function ensures backend is running, creates es_cls, and ensures readiness for data operations"""
        SwiftDataBackend.__throwing_integrity_check()
        # builds the elastic search document object and index, or from cache, from the swiftdata object
        es_cls, es_index = SwiftDataInternal.build_es_class_from_swift_class(cls, index)
        return (SwiftDataBackend.client.es, es_cls, es_index) if with_index else (SwiftDataBackend.client.es, es_cls)

    @staticmethod
    def create_stub(id, cls_name, index, tags=None):
        """Builds /{index}/{tag1}/{value1}/{tag2}/{value2}/swift.{cls_name}/ and swift.{index}.{cls_name}.{id}.json"""
        if tags is None: tags = dict()
        directory = create_programmatic_directory(SwiftDataBackend.swiftdata_base_directory, tags)
        directory = os.path.join(directory, "_index", index, f"swift.{cls_name}/")
        if id is None: return directory.lower()
        return os.path.join(directory, SwiftDataBackend.__stub_basename(index, cls_name, id)).lower()

    @staticmethod
    def __stub_basename(index, cls_name, id): return f"swift.{index}.{cls_name}.{id}.json".lower()

    @staticmethod
    def __throwing_integrity_check():
        if SwiftDataBackend.server is None:
            raise RuntimeError("SwiftDataBackend is not running and must be started before using its ElasticSearch.")
        if SwiftDataBackend.client is None:
            raise RuntimeError("SwiftDataBackend has been deleted and this should not happen.")


########################################################################################################################
# internal use code only
########################################################################################################################


class SwiftDataInternal(object):

    already_built = dict()  # map from SD base_cls => (ESD, ESD Index)  objects already built.
    fieldmap = {cls.__name__: cls for cls in [Keyword, Text, Integer, Float, Date, Boolean, DenseVector, GeoPoint]}

    @staticmethod
    def build_es_class_from_swift_class(swift_cls, prefix=None):
        """Builds ElasticSearchDocument equivalents of SwiftData; can be dependent on previously built classes"""
        # NOTE: applet is a prefix to ensure that ESD are not transferable across projects in the same ES Service.
        prefix = "" if prefix is None else f"{prefix}."
        es_cls_name = f"{prefix}{swift_cls.__name__}.ElasticSearchDocument"
        if es_cls_name in SwiftDataInternal.already_built: return SwiftDataInternal.already_built[es_cls_name]

        es_cls = type(es_cls_name, (Document,), dict())  # Build the base ESD with no attributes.
        for field in dataclasses.fields(swift_cls):
            if hasattr(field.type, "__es_field_cls_name"):  # expect every non-SwiftData build basic field to have these
                es_field_cls_name = getattr(field.type, "__es_field_cls_name")
                es_parameters = getattr(field.type, "__es_parameters")  # expect every SwiftData class to have these
            else:  # using a derived class
                try: es_parameters, es_field_cls_name = field.type.__origin__ == dict(multi=True), field.type.__args__[0].__name__
                except AttributeError: es_parameters, es_field_cls_name = dict(multi=False), field.type.__name__
            if es_field_cls_name in SwiftDataInternal.fieldmap:
                es_field = SwiftDataInternal.fieldmap[es_field_cls_name](**es_parameters)
            elif es_field_cls_name in SwiftDataInternal.already_built:
                # if specified as list[EXISTING] need to do the split here; base_cls=EXISTING
                es_field = SwiftDataInternal.already_built[es_field_cls_name](**es_parameters)
            else: raise KeyError(f"SwiftData {swift_cls.__name__} has unsupported field {field.name}={field.type}")
            setattr(es_cls, field.name, es_field)  # add to the base ESD

        # create Index for each
        es_index = Index(f"index.{es_cls.__name__}".lower())
        es_index.document(es_cls)
        SwiftDataInternal.already_built[es_cls_name] = [es_cls, es_index]
        return SwiftDataInternal.already_built[es_cls_name]

    @staticmethod
    def swiftdata_obj_es_init(swift_obj): return vars(swift_obj) | dict(meta=dict(id=swift_obj.id))

    @staticmethod
    def es_obj_swiftdata_init(es_obj):
        """Performs the same as Document.to_dict() which is broken for now because of the dynamic ES creation."""
        return es_obj.to_dict()
