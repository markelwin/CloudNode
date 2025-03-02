from cloudnode.base.core.search.search import MeilisearchServer, MeilisearchClient, MeilisearchQueryHelper, SearchQueryHelper
from cloudnode.base.core.lightweight_utilities.filesystem import FileSystem
from cloudnode.base.core.lightweight_utilities.cloudnode import create_programmatic_directory
from cloudnode.base.core.swiftdata.models import sd, descriptions_of_sd
from cloudnode.config import RuntimeConfig
import meilisearch
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


class SwiftData:
    id: sd.string()
    ts: sd.timestamp()

    @classmethod
    def _fields(cls):
        """This method replaces dataclasses.fields to move SwiftData away from dataclasses to normal class definition"""
        fields = dict()
        for _super in cls.__bases__:
            if issubclass(_super, SwiftData): fields = dict(_super._fields()) | fields
        if "__annotations__" in cls.__dict__:
            fields = cls.__dict__["__annotations__"] | fields
        return fields.items()

    def __init__(self, **data):
        """This method replaces the dataclasses implicit __init__ constructor which populates each of its attributes"""
        for key, value in data.items(): setattr(self, key, value)

    @classmethod
    def __init_subclass__(cls):
        """This method is called after any SubClass /definition/ to identify fields with defined set/get methods."""
        # NOTE: there are instances in which fields (i.e., timestamps) should have data wranglers when set or get (i.e.
        # the user may set the timestamp field with a string instead of a datetime; which is then parsed in the setter
        # of the field according to the timestamp.upon_set(value) function, if defined; similarly for getters. This lets
        # dataclass use conventional styles (strings) for storage on object by allows the user to have the full suite of
        # expectations (i.e., gps = "lat,lng" or ["lat", "lng"] or [lat, lng]) all while seamlessly connecting from the
        # dataclass to its disk json to its storage database document (and how swiftdata handles ingestion to database).
        # In short, this defines get/set data wranglers for any special SwiftData datatype (i.e., sd.timestamp())
        for fieldname, fieldtype in cls._fields():
            private = f"__{fieldname}"  # create a private storage attribute for each user defined attribute
            setattr(cls, private, None)
            if hasattr(fieldtype, "upon_get"):  # if no upon_get exists simply return the __variable storage value
                def getter(_self, _private=private, _fieldtype=fieldtype): return _fieldtype.upon_get(getattr(_self, _private))
            else:
                def getter(_self, _private=private): return getattr(_self, _private)
            getter.__name__ = f"getter_{cls.__name__}_{fieldname}"
            if hasattr(fieldtype, "upon_set"):  # if no upon_set exists simply store any value directly to __variable
                def setter(_self, _value, _private=private, _fieldtype=fieldtype):
                    return setattr(_self, _private, _fieldtype.upon_set(_value))
            else:
                def setter(_self, _value, _private=private): return setattr(_self, _private, _value)
            setter.__name__ = f"setter_{cls.__name__}_{fieldname}"
            setattr(cls, fieldname, property(getter, setter))

    @classmethod
    def empty(cls):
        """Initializer that populates all fields with empty objects. Useful for updating or merging records."""
        return cls(**{name: None for (name, _) in cls._fields()})

    @classmethod
    def new(cls, id=None, ts=None, **data):
        """Initializer that accepts missing values (set to empty); and sets .id and .ts if not provided."""
        if data is None: data = dict()
        values = {name: (data[name] if name in data else None) for (name, _) in cls._fields()}
        if id is None and "id" not in data: values["id"] = uuid.uuid4().hex.lower()
        if id is not None: values["id"] = str(id).lower()  # if id or ts are set these values will override any in data
        if ts is None and "ts" not in data: values["ts"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if ts is not None: values["ts"] = ts
        # because constructors do not call setters unless explicit within the init we will explicitly use setters
        # NOTE: this is an important detail: calling __init__(**data) directly would not access wranglers: use .new()
        for (fieldname, fieldtype) in cls._fields():
            if hasattr(fieldtype, "upon_set") and fieldname in values:  # upon_set then upon_get allows any user input
                values[fieldname] = fieldtype.upon_set(values[fieldname])
                if hasattr(fieldtype, "upon_get") and fieldname in values:
                    values[fieldname] = fieldtype.upon_get(values[fieldname])
        # this section explicitly constructs fields which may be SwiftData objects themselves; or expected to be lists.
        for (fieldname, fieldtype) in cls._fields():
            if fieldname in values:
                try: is_list, field_cls = fieldtype.__origin__ == list, fieldtype.__args__[0]  # both are equally fast
                except AttributeError: is_list, field_cls = False, fieldtype
                if issubclass(field_cls, SwiftData):  # map data to class explicitly
                    if values[fieldname] is not None:
                        if is_list: values[fieldname] = [field_cls.new(**d) for d in values[fieldname]]
                        else: values[fieldname] = field_cls.new(**values[fieldname])
        return cls(**values)

    def as_dict(self):
        """simply converts swiftdata to dict and uses any upon_disk_storage handlers if data to be saved to disk"""
        _as_dict = {name: getattr(self, name) for (name, _) in self._fields()}
        for (fieldname, fieldtype) in self.__class__._fields():
            if hasattr(fieldtype, "upon_disk_storage") and fieldname in _as_dict:
                _as_dict[fieldname] = fieldtype.upon_disk_storage(_as_dict[fieldname])
            try: is_list, field_cls = fieldtype.__origin__ == list, fieldtype.__args__[0]
            except AttributeError: is_list, field_cls = False, fieldtype
            if issubclass(field_cls, SwiftData):  # map data to class explicitly
                if is_list: _as_dict[fieldname] = [d.as_dict() for d in _as_dict[fieldname]]
                else: _as_dict[fieldname] = _as_dict[fieldname].as_dict()
        return _as_dict

    def __repr__(self): return f"<{self.__class__.__name__} id={self.id}>"

    # The methods below this line are written to interact with both filesystem storage and the search database.

    def save(self, silo, exist_ok=True, db=False):
        if db:
            _, db_index = SwiftDataBackend.operation_context(silo, self.__class__)
            results = db_index.add_documents([self.as_dict()], primary_key="id")
            SwiftDataBackend.client.meilisearch_wait_for_task(db_index, results)
            return True
        else:
            stub = SwiftDataBackend.create_stub(self.id, self.__class__.__name__, silo)
            if not exist_ok and FileSystem.easy_exists(stub):
                raise RuntimeError(f"item exists in database {self}")
            as_dict = self.as_dict()
            FileSystem.easy_upload(io.StringIO(json.dumps(as_dict)), stub)
        return True

    @classmethod
    def saveAll(cls, silo, swift_objs, exist_ok=True, db=False):
        if db:
            logger.warning(".saveAll() does not protect against exist_ok=False.")
            _, db_index = SwiftDataBackend.operation_context(silo, cls)
            results = db_index.add_documents([obj.as_dict() for obj in swift_objs], primary_key="id")
            SwiftDataBackend.client.meilisearch_wait_for_task(db_index, results)
            return True
        else:
            [obj.save(silo, exist_ok=exist_ok, db=False) for obj in swift_objs]

    @classmethod
    def delete(cls, silo, id, db=False):
        if db:
            _, db_index = SwiftDataBackend.operation_context(silo, cls)
            results = db_index.delete_document(id, primary_key="id")
            SwiftDataBackend.client.meilisearch_wait_for_task(db_index, results)
            return True
        else:
            stub = SwiftDataBackend.create_stub(id, cls.__name__, silo)
            return FileSystem.easy_delete(stub)

    @classmethod
    def get(cls, silo, id, db=False):
        if db:
            _, db_index = SwiftDataBackend.operation_context(silo, cls)
            if isinstance(id, (tuple, list)):
                results = MeilisearchQueryHelper.meilisearch_mget_documents(db_index, id)
                items = [cls.new(**r) for r in results["hits"]]
                items = {_id: None for _id in id} | {item.id: item for item in items}  # returns dict=None for not exist
                return [items[_id] for _id in id]  # as list
            else:
                results = db_index.get_document(id)
                return cls.new(**vars(results))
        else:
            if not isinstance(id, (tuple, list)): id = [id]
            objects = []
            for _id in id:
                if not cls.exists(silo, _id): result = None
                else:
                    stub = SwiftDataBackend.create_stub(id, cls.__name__, silo)
                    file_obj = FileSystem.easy_download(stub)
                    result = cls.new(json.load(file_obj))
                objects.append(result)
            return objects

    @classmethod
    def getAll(cls, silo, db=False, limit=50):
        if db:
            _, db_index = SwiftDataBackend.operation_context(silo, cls)
            results = MeilisearchQueryHelper.meilisearch_getall_documents(db_index, limit=limit)
            return  [cls.new(**vars(r)) for r in results.results]
        else:
            objs = []
            for id in cls.list(silo)[:limit]:
                stub = SwiftDataBackend.create_stub(id, cls.__name__, silo)
                file_obj = FileSystem.easy_download(stub)
                objs.append(cls.new(**json.load(file_obj)))
            return objs

    @classmethod
    def exists(cls, silo, id, db=False):
        if db:
            _, db_index = SwiftDataBackend.operation_context(silo, cls)
            try:
                db_index.get_document(id)
                return True
            except meilisearch.errors.MeilisearchApiError as e:
                if e.status_code == 404: return False
                else: raise
        else:
            stub = SwiftDataBackend.create_stub(id, cls.__name__, silo)
            return FileSystem.easy_exists(stub)

    @classmethod
    def list(cls, silo, db=False):
        if db:
            _, db_index = SwiftDataBackend.operation_context(silo, cls)
            return MeilisearchQueryHelper.meilisearch_list_documents(db_index)
        else:
            directory = SwiftDataBackend.create_stub(None, cls.__name__, silo)
            filenames = FileSystem.easy_listdir(directory)
            pattern = re.compile(f"swift.{silo}.{cls.__name__}.(.*?).json".lower())
            return [pattern.match(filename).group(1) for filename in filenames if pattern.match(filename)]


    @classmethod
    def count(cls, silo, db=False):
        if db:
            _, db_index = SwiftDataBackend.operation_context(silo, cls)
            return db_index.get_stats().number_of_documents
        else:
            return len(cls.list(silo))

    @classmethod
    def create_index(cls, silo, exist_ok=False):
        """makes explicit for the user the creation of the search index for the first time"""
        db_client, db_index = SwiftDataBackend.operation_context(silo, cls)
        if not SwiftDataBackend.client.index_exists(db_index.uid):
            logger.info(f"creating index {db_index.uid} for {cls.__name__} for its first use")
            db_client.create_index(db_index.uid, dict(primaryKey="id"))  # create, and filterable.
            db_client.index(db_index.uid).update_filterable_attributes([fieldname for fieldname, _ in cls._fields()])
        else:
            if exist_ok: return
            raise RuntimeError(f"index {db_index.uid} for {cls.__name__} already exists")

    @classmethod
    def delete_index(cls, silo):
        _, db_index = SwiftDataBackend.operation_context(silo, cls)
        if SwiftDataBackend.client.index_exists(db_index.uid):
            results = SwiftDataBackend.client.client.delete_index(db_index.uid)
            SwiftDataBackend.client.meilisearch_wait_for_task(db_index, results)

    @classmethod
    def search(cls, silo, search="", opt_params=None, limit=50):
        """performs a search using meilisearch search construction"""
        _, db_index = SwiftDataBackend.operation_context(silo, cls)
        if opt_params is None: opt_params = dict()
        if limit is not None: opt_params = opt_params | dict(limit=limit)
        results = db_index.search(search, opt_params)
        return [cls.new(**r) for r in results["hits"]]

    @classmethod
    def search_bar(cls, silo, s, limit=50, only_fields=None, exclude_fields=None):
        """performs a search bar like query on a string with field prompts, i.e., "cast: david year: 1980" """
        components = SearchQueryHelper.search_bar(s)
        fieldnames = [fieldname for fieldname, fieldtype in cls._fields()]
        keep = [c["field"] in fieldnames or c["field"] is None for c in components]
        misconfigured = [c for i, c in enumerate(components) if not keep[i]]
        components = [c for i, c in enumerate(components) if keep[i]]
        if len(misconfigured) != 0: logger.warning(f"fields misspelled or non-existent: fields={misconfigured}")
        search, opt_params = MeilisearchQueryHelper.meilisearch_construct_complex_query_from_search_bar(components, only_fields=only_fields, exclude_fields=exclude_fields)
        if limit is not None: opt_params = opt_params | dict(limit=limit)
        return cls.search(silo, search, opt_params)

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


class SwiftDataBackend:

    server = None  # global server
    client = None  # global client
    swiftdata_base_directory = "file://" + os.path.join(RuntimeConfig.directory_base_local, "_subsystem/swiftdata/")

    def __init__(self, database_hostport, database_password):
        self.database_hostport = database_hostport  # create client here; but also wait for active server?
        self.database_password = database_password  # always require hostport? otherwise looks good?

        # self.start_server(exist_ok=True)  # disabled temporarily
        SwiftDataBackend.server = True  # instead of MeilisearchServer variable, while disabled
        SwiftDataBackend.client = MeilisearchClient(hostport=database_hostport, passkey=database_password)
        SwiftDataBackend.client.wait_for_active_server()

    def start_server(self, exist_ok=False):
        if not exist_ok and (SwiftDataBackend.server is not None or SwiftDataBackend.client is not None):
            raise RuntimeError("SwiftDataBackend has previously been started and is not intended for parallelization.")
        SwiftDataBackend.server = MeilisearchServer(
            hostport=self.database_hostport, passkey=self.database_password, exist_ok=exist_ok)
        return self

    def stop_server(self):
        if self.server is None: logger.error("SwiftDataBackend server has not been created. did you not run .start()")
        self.server.stop()

    @staticmethod
    def operation_context(silo, swift_cls):
        """Convenience function ensures backend is running, creates silo cls index if necessary, and data operations"""
        SwiftDataBackend.__throwing_integrity_check()
        # builds the database search index, or from cache, from the swiftdata object
        index_name = f"{silo}___{swift_cls.__name__}".lower()
        return SwiftDataBackend.client.client, SwiftDataBackend.client.client.index(index_name)

    @staticmethod
    def create_stub(id, cls_name, silo, tags=None):
        """Builds /{index}/{tag1}/{value1}/{tag2}/{value2}/swift.{cls_name}/ and swift.{silo}.{cls_name}.{id}.json"""
        if tags is None: tags = dict()
        directory = create_programmatic_directory(SwiftDataBackend.swiftdata_base_directory, tags)
        directory = os.path.join(directory, "_silo", silo, f"swift.{cls_name}/")
        if id is None: return directory.lower()
        return os.path.join(directory, SwiftDataBackend.__stub_basename(silo, cls_name, id)).lower()

    @staticmethod
    def __stub_basename(silo, cls_name, id): return f"swift.{silo}.{cls_name}.{id}.json".lower()

    @staticmethod
    def __throwing_integrity_check():
        if SwiftDataBackend.server is None:
            raise RuntimeError("SwiftDataBackend is not running and must be started before using its search database.")
        if SwiftDataBackend.client is None:
            raise RuntimeError("SwiftDataBackend has been deleted and this should not happen.")
