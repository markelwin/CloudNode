from cloudnode.base.core.thirdparty.DockerClient import DockerClient
from cloudnode.base.core.lightweight_utilities.misc import TemporarilySuppressLoggingEqualOrHigher
from cloudnode.config import RuntimeConfig
from elasticsearch_dsl import Search, Q
from elasticsearch import Elasticsearch, helpers
import elasticsearch.exceptions
import tempfile
import urllib3
import datetime
import yaml
import time
import re
import os

import logging
logger = logging.getLogger(__name__)

##############################################################################################################
# Elastic Search
##############################################################################################################
# NOTE: For tutorial: https://dylancastillo.co/elasticsearch-python/amp/
# NOTE: For latest docker version: https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html

########################################################################################################################
# NOTES ON QUERY BUILDING
########################################################################################################################
# SPEED: There are two types of queries: scoring (match, etc) and non-scoring (filter; bool). Non-scoring are much much
# faster. Non-scoring queries (don't calculate relevance) and are cached for subsequent calls: use as often as possible.
# FORM: "must" is AND; "filter" is AND without scoring; "should" is OR; "must_not" is XOR; "range" is range but slow. A
# useful trick is to transform ranges into atomic selections; i.e., 24-hour day into 5 minute arrays and match directly.
# https://medium.com/gojekengineering/elasticsearch-the-trouble-with-nested-documents-e97b33b46194
# ANALYZE: see how content is analyzed. GET localhost:9200/INDEX/_analyze -d dict(field=value)
#
# NESTED (Parent/Child): Parent and child documents are two separate documents; the parent must be inserted first, then
# the child is inserted, with the key field of parent assigning the child to the parent. Each document is inserted
# independently, and both will be distributed into the same shard, but are not guaranteed to be in the same Lucine
# segment (index). The parent child relation is maintained in a memory relation table so that retrieval of the parent
# retrieves the child too. The advantage of nested is that each can be updated independently, so is a most appropriate
# for frequently updating multi-level relationships. Q("nested", path="sub", query=Q("exists", field="sub.value"))
#
# SNAPSHOTS: For ElasticSearch indices to be stored in Google Cloud Storage (as one cloud based example)
# NOTE: https://www.elastic.co/guide/en/cloud/current/ec-gcs-snapshotting.html
# NOTE: https://www.elastic.co/guide/en/elasticsearch/reference/current/repository-gcs.html


class ElasticSearchServer(object):

    docker_container = "docker.elastic.co/elasticsearch/elasticsearch:8.15.1"
    port = "9200"
    name = "elasticsearch"

    def __init__(self, password=None, exist_ok=False, run_ok=False):
        self.docker = DockerClient()
        name = ElasticSearchServer.name
        if self.docker.container_is_built(name):
            if not exist_ok:
                raise RuntimeError(f"ElasticSearch server already exists: {name}")
            self.container = self.docker.client.containers.get(name)
            if DockerClient.container_is_running(self.container):
                if run_ok:
                    logger.info(f"ElasticSearch server already running: {name}")
                    return
                raise RuntimeError(f"ElasticSearch server already running: {name}")
            logger.info(f"ElasticSearch server restarting procedure (about 30 seconds): {name}")
            self.start()
            return

        # container is not built
        logger.info(f"ElasticSearch server startup procedure (about 30 seconds): {name}")
        environment = {"discovery.type": "single-node",
                       "xpack.security.http.ssl.enabled": "false",
                       "xpack.license.self_generated.type": "trial"}
        if password is not None: environment.update(ELASTIC_PASSWORD=password)
        directory = os.path.join(RuntimeConfig.directory_base_local, "_subsystem/swiftdata/_snapshots/elasticsearch/")
        mounts = [dict(target=directory, source=directory, type="bind", read_only=False)]
        self.docker.container_build(ElasticSearchServer.docker_container,
                                    ElasticSearchServer.port,
                                    name=name, mounts=mounts, detach=True,
                                    environment=environment, censor=["ELASTIC_PASSWORD"])

        # now we edit its elasticsearch.yaml to accept snapshots and restart
        tmp = tempfile.NamedTemporaryFile(suffix=".yaml", delete=True)
        in_container_config_yaml = "/usr/share/elasticsearch/config/elasticsearch.yml"
        self.docker.copy_from_container(name, in_container_config_yaml, tmp.name)
        with open(tmp.name, "r") as f: config = yaml.safe_load(f)
        if "path.repo" not in config: config["path.repo"] = [directory]
        if directory not in config["path.repo"]: config["path.repo"].append(directory)
        with open(tmp.name, "w") as f: yaml.safe_dump(config, f)
        self.docker.copy_to_container(name, tmp.name, in_container_config_yaml)
        self.docker.container_stop(name, wait=True)
        self.docker.container_start(name)

    @staticmethod
    def force_delete():
        client = DockerClient()
        if client.container_is_built(ElasticSearchServer.name):
            client.container_remove(ElasticSearchServer.name, force=True)

    @staticmethod
    def stop(not_exist_ok=False):
        DockerClient().container_stop(ElasticSearchServer.name, not_exist_ok=not_exist_ok, wait=True)

    @staticmethod
    def start(not_exist_ok=False):
        DockerClient().container_start(ElasticSearchServer.name, not_exist_ok=not_exist_ok)


class ElasticSearchClient(object):

    def __init__(self, hostport=None, password=None):
        if hostport is None: hostport = f"127.0.0.1:{ElasticSearchServer.port}"
        self.hostport = hostport
        kwargs = dict(hosts=[f"http://{hostport}"])  # SSL would use https://
        if password is not None: kwargs["basic_auth"] = ("elastic", password)
        self.es = Elasticsearch(**kwargs)

    def is_active(self):
        """Convenience method that checks for active connection: will fail if either ping or connection fails."""
        try:
            with TemporarilySuppressLoggingEqualOrHigher(logging.ERROR):
                return self.es.ping(error_trace=True, human=False, pretty=True)
        except urllib3.exceptions.SSLError as e:
            logger.error("SSL Certification not provided or incorrect.", exc_info=True)
            return False
        except Exception as e:
            logger.warning(f"Connection {self.es} has failed. Did not yet ping.")
            return False

    def wait_for_active(self, timeout_s=None):
        """Simple method for blocking until the ElasticSearch server is running; will throw an error at timeout_s."""
        s = time.time()
        until = "indefinitely" if timeout_s is None else f"{timeout_s} seconds"
        while not self.is_active():
            if timeout_s is not None and time.time() - s > timeout_s:
                raise TimeoutError(f"ElasticSearch server has remained still inactive after {timeout_s} seconds.")
            logger.info(f"Waiting {until} for ES {self.hostport} to Launch. Pausing one second at {time.ctime()}")
            time.sleep(1)

    def index_exists(self, index_name):
        """Identify whether an INDEX exists."""
        # XHEAD "/<index_name>?pretty" returns 200 if exists and 404 if not.
        response = self.perform_request("HEAD", f"/{index_name}?pretty")
        if response.meta.status == 404: return False
        if response.meta.status == 200: return True
        raise ValueError(f"ElasticSearch index_exists {index_name} response code not understood: {response.meta}")

    def snapshot_save(self, applet, save_name=None):
        """Creates a snapshot SAVE_NAME within APPLET; i.e., save_name=today_date; applet=movies_project"""
        # NOTE: Snapshots instances are incremental, so each update via PUT pushes only changes.
        # NOTE: ElasticSearch requires all field names to be lowercase
        # PUT /_snapshot/APPLET/INSTANCE
        if save_name is None: save_name = datetime.datetime.now().isoformat().lower()
        logger.info(f"SNAPSHOT SAVE {applet} {save_name}")
        return self.perform_request("PUT", f"/_snapshot/{applet.lower()}/{save_name.lower()}")

    def snapshot_info(self, applet, save_name):
        """Retrieves information and statistics of the SAVE_NAME snapshot, including its updating progress if any"""
        # NOTE: ElasticSearch requires all field names to be lowercase
        # GET /_snapshot/APPLET/INSTANCE
        logger.info(f"SNAPSHOT INFO {applet} {save_name}")
        return self.perform_request("GET", f"/_snapshot/{applet.lower()}/{save_name.lower()}")

    def snapshot_load(self, applet, save_name, indices=None):
        """Retrieves snapshot then loads its state into the search databases."""
        # NOTE: must close indices before loading them: POST INDEX_NAME/_close
        # NOTE: ElasticSearch requires all field names to be lowercase
        # NOTE: POST /_snapshot/APPLET/SAVE_NAME/_restore { "indices": "*" }
        if indices is None: indices = ["*"]
        logger.info(f"INDICES CLOSE {applet} {indices}")
        open_indices_s = self.perform_request("GET", "/_cat/indices")
        open_indices_s = [line.strip() for line in open_indices_s.split("\n") if line.strip() != ""]
        open_indices = [line.split(" ")[2] for line in open_indices_s if len(line.split(" ")) > 3]
        [self.perform_request("POST", f"/{index}/_close") for index in indices if index in open_indices]
        logger.info(f"SNAPSHOT LOAD {applet} {save_name}")
        return self.perform_request("POST", f"/_snapshot/{applet.lower()}/{save_name.lower()}/_restore", data=dict(indices=indices))

    def snapshot_latest(self, applet):
        """Convenience function for getting the most recent instance for reloading state of an ElasticSearch index"""
        results = self.snapshot_list(applet)
        if results is None: return None, None
        return results[0]

    def snapshot_exists(self, applet):
        """Verifies that applet exists to create snapshots in it."""
        # NOTE: POST /_snapshot/<repository>/_verify
        logger.info(f"SNAPSHOT EXISTS {applet}")
        try:
            self.perform_request("POST", f"/_snapshot/{applet.lower()}/_verify")
        except elasticsearch.exceptions.NotFoundError as e: return False
        except Exception as e: raise e
        return True

    def snapshot_directory_set(self, directory, applet):
        """Sets a directory as a snapshot save location; creates and registers snapshot if necessary"""
        # PUT /_snapshot/my_repository data=(type="fs", settings=dict(location="my_backup_location"))
        data = dict(type="fs", settings=dict(location=directory))
        return self.perform_request("PUT", f"/_snapshot/{applet.lower()}/", data=data)

    def snapshot_list(self, applet, n_most_recent=10):
        """Retrieves n_most_recent snapshots sorted in chronological order with the latest at index 0."""
        # NOTE: ElasticSearch requires all field names to be lowercase
        # NOTE: GET /_snapshot/my_repository/*?sort=start_time&size=n_most_recent&order=desc
        logger.info(f"SNAPSHOT LIST {applet}")
        results = self.perform_request("GET", f"/_snapshot/{applet.lower()}/*?sort=start_time&size={n_most_recent}&order=desc")
        if "snapshots" not in results.body: return None
        return [r["snapshot"] for r in results.body["snapshots"]]

    def perform_request(self, method, path, data=None):
        """Convenience function bounding calls to ElasticSearch service to ElasticSearch connection, i.e., using it"""
        headers = {} if data is None else {"accept": "application/json", "content-type": "application/json"}
        return self.es.perform_request(method, path, headers=headers, body=data)

    def streaming_bulk_upsert(self, objs):
        """Creates a streaming bulk insert or upsert: ElasticSearch seems to suggest these are identical actions."""
        # NOTE: objs are elasticsearch_dsl Documents
        # NOTE: is superfluous: https://github.com/elastic/elasticsearch-dsl-py/issues/403#issuecomment-392803588
        # NOTE: optimal bulk size? total MB is what matters, about 50MB (100MB max); 5MB ideal, about 1K to 5K docs per
        # NOTE: https://stackoverflow.com/questions/18488747/what-is-the-ideal-bulk-size-formula-in-elasticsearch
        return list(helpers.streaming_bulk(self.es, [obj.to_dict(True) for obj in objs]))

    def count(self, index):
        """Returns count of all documents in index."""
        self.es.indices.refresh(index=index)
        result = self.es.cat.count(index=index, params={"format": "json"})
        return int(result[0]["count"]) if (result is not None and isinstance(result, list) and "count" in result[0]) else None


class ElasticSearchDslClient(object):
    """Convenience class for useful ElasticSearch queries using the elasticsearch-dsl objects"""

    @staticmethod
    def getAll(es, es_cls, max_results=50):
        """Returns all objects of es_cls (in its implied index)"""
        return ElasticSearchDslClient.perform_dsl_query(es, es_cls, dsl_q=None, max_results=max_results)

    @staticmethod
    def listAll(es, es_index, es_cls):
        """Returns ids of all objects of es_cls (in its implied index)"""
        s = Search(using=es, index=es_index, doc_type=es_cls)
        s = s.source([])  # only get ids, otherwise `fields` takes a list of field names
        return [h.meta.id for h in s.scan()]

    @staticmethod
    def search_bar(s):
        """Creates an ElasticSearch Query using a familiar search bar: ~title:bucket cast:"jack nicholson"""
        # NOTE: ~title:bucket cast:"jack nicholson" bruce
        # NOTE: ~ is NOT.
        # NOTE: AND is implied between fields. OR can be used with multiple phases to search into a field.
        # NOTE: a phase in quotes implies a direct match of that phrase: i.e., "jack nicholson" does not match "jack"
        # NOTE: all <field>: text next <field>: queries into field, i.e., search cast field for "jack nicholson" bruce
        # NOTE: multiple phrases within a <field>: implies OR: i.e., "phrase1" word2 => "phrase1" OR word2
        # (Q("match_phrase", cast='jack nicholson') | Q("match", cast='bruce')) & Q("bool", filter=[~Q("match", title="bucket")])
        items = s.lower().split(" ")
        is_field = [i for i, item in enumerate(items) if ":" in item] + [len(items)]  # makes next line one line
        items = [" ".join(items[is_field[i]:is_field[i+1]]) for i in range(len(is_field)-1)]
        components = []
        for i, item in enumerate(items):
            q = item.split(":")  # e.g., ~title:bucket ==> is_not=True, q_key=title
            qfield, qvalue = q[0], ":".join(q[1:])
            is_not = qfield.startswith("~")
            field = qfield[1:] if is_not else qfield  # ~title => title   or title => title
            pattern = '"([^"]*)"'
            quoted_strings = [g.group(1) for g in re.finditer(pattern, qvalue)]
            non_quoted_strings = [p.strip() for p in re.sub(pattern, "", qvalue).split(" ") if p.strip() != ""]
            ops = []
            for qs in quoted_strings: ops.append(Q(name_or_query="match_phrase", **{field: qs}))
            for qs in non_quoted_strings: ops.append(Q(name_or_query="match", **{field: qs}))
            if len(ops) == 0: continue
            op = ops[0]
            for o in ops[1:]: op = op.__or__(o)
            if is_not: op = op.__invert__()
            components.append(op) if i == 0 else components.append(Q(name_or_query="bool", filter=[op]))
        if len(components) == 0: raise RuntimeError("No query found.")
        query = components[0]
        for c in components[1:]: query = query.__and__(c)
        return query

    ####################################################################################################################
    # Queries
    ####################################################################################################################

    # @staticmethod
    # def search_any(field, values):
    #     """Returns all matches that contain one of the values in values in field."""
    #     matches = [Q('match', **{field: v}) for v in values]
    #     return Q('bool', should=matches, minimum_should_match=1)

    @staticmethod
    def perform_dsl_query(es, es_cls, dsl_q, max_results=50):
        """Executes queries using the elasticsearch-dsl query structured objects"""
        s = es_cls.search(using=es).extra(size=max_results)
        r = s.execute() if dsl_q is None else s.query(dsl_q).execute()
        es_objs = []
        for h in r["hits"]["hits"]:
            h = h.to_dict()
            d = es_cls(**h["_source"])
            d.meta.id = h["_id"]
            es_objs.append(d)
        return es_objs
