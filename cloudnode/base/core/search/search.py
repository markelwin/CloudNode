from cloudnode.base.core.lightweight_utilities.sysops import this_binary_is_running
from meilisearch.errors import MeilisearchApiError
import meilisearch
import subprocess
import string
import shutil
import time
import os
import re

import logging
logger = logging.getLogger(__name__)


class MeilisearchServer:


    def __init__(self, binary="meilisearch", hostport="http://127.0.0.1:7700", db_path="data.ms/", passkey=None, exist_ok=False):

        # Note: ensure the binary is found
        if os.path.isabs(binary):
            logger.info(f"absolute path detected. starting using binary={binary}")
        else:
            if shutil.which(binary) is None:
                logger.error(f"binary={binary} not in $PATH. please specify absolute filename of binary or reinstall.")
            else: binary = f"./{binary}"

        # Note: https://www.meilisearch.com/docs/learn/self_hosted/configure_meilisearch_at_launch
        cmd = f"{binary} --experimental-contains-filter --db-path {db_path} --http-addr='{hostport}'"
        logger.info(f"initializing with [passkey obscured] cmd={cmd}")
        cmd += f" --master-key={passkey}"
        self.binary = binary
        self.cmd = cmd
        self.exist_ok = exist_ok
        self.subprocess = None

    def start(self):
        if this_binary_is_running(os.path.basename(self.binary)):
            if self.exist_ok:
                logger.info(f"binary={self.binary} process is already running. please inspect 'ps' if this is unexpected")
                return
            else: raise RuntimeError(f"binary={self.binary} process is already running.")
        self.subprocess = subprocess.Popen([p.strip() for p in self.cmd.split() if len(p.strip()) != 0])

    def stop(self):
        if self.subprocess is None:
            logger.error("subprocess has not been created. did you not run .start()")
        self.subprocess.kill()


class MeilisearchClient:

    def __init__(self, hostport="http://127.0.0.1:7700", passkey=None):
        self.client = meilisearch.Client(hostport, passkey)

    def is_active_server(self):
        """Convenience method that checks for active connection: will fail if either ping or connection fails."""
        try:
            status = self.client.health()
            return True if status.get("status") == "available" else False
        except Exception as e:
            logger.warning(f"Connection {self.client} has failed. Did not yet ping.")
            return False

    def wait_for_active_server(self, timeout_s=None):
        """Simple method for blocking until the server is running; will throw an error at timeout_s."""
        s = time.time()
        until = "indefinitely" if timeout_s is None else f"{timeout_s} seconds"
        while not self.is_active_server():
            if timeout_s is not None and time.time() - s > timeout_s:
                raise TimeoutError(f"Meilisearch server has remained still inactive after {timeout_s} seconds.")
            logger.info(f"Waiting {until} for {self.client.config.url} to become active. pausing one second at {time.ctime()}")
            time.sleep(1)

    def index_exists(self, index_name):
        """Identify whether an INDEX exists."""
        try:
            self.client.index(index_name).fetch_info()
            return True
        except MeilisearchApiError as e:
            if e.status_code == 404: return False
            raise

    @staticmethod
    def meilisearch_print_error(error):
        return f"code={error['code']} error={error['message']} url={error['link']}"

    @staticmethod
    def meilisearch_wait_for_task(index, results, sleep_s=0.1, timeout_s=30):
        task_uid = results.task_uid
        result = index.get_task(task_uid)
        print(f"Task {task_uid} status: {result.status}")
        poll_start_s = time.perf_counter()
        while result.status not in ["succeeded", "failed"]:
            result = index.get_task(task_uid)
            print(f"Task {task_uid} status: {result.status} so_far_s={time.perf_counter()-poll_start_s}")
            if time.perf_counter() > poll_start_s + timeout_s:
                raise TimeoutError(f"Task {task_uid} status: timeout={timeout_s}")
            time.sleep(sleep_s)
        if result.status == "failed":
            raise RuntimeError(MeilisearchClient.meilisearch_print_error(result.error))


class MeilisearchQueryHelper:
    """useful Meilisearch queries in more common language"""

    @staticmethod
    def meilisearch_mget_documents(db_index, ids, not_found_value=None):
        """the fastest way to do mget (multiple get) across a list of ids"""
        _filter = "[" + ",".join([f"'{id}'" for id in ids]) + "]"
        return db_index.search("", dict(filter=f"id IN {_filter}"))

    @staticmethod
    def meilisearch_getall_documents(db_index, limit=None):
        if limit is None: limit = db_index.get_stats().number_of_documents
        return db_index.get_documents(dict(limit=limit))

    @staticmethod
    def meilisearch_list_documents(db_index):
        results = db_index.search("", dict(attributesToRetrieve=["id"]))
        return [r["id"] for r in results["hits"]]

    @staticmethod
    def meilisearch_construct_complex_query_from_search_bar(components, only_fields=None, exclude_fields=None):
        search, filters = [], []
        for component in components:
            field = None if component["field"] is None else component["field"].lower()
            if only_fields is not None and field not in only_fields: continue
            if exclude_fields is not None and field in exclude_fields: continue
            queries = [op.get("s") for op in component["ops"]]
            if field is None:
                search.append(" ".join([f'"{q}"' for q in queries]))
                continue
            as_filter = "(" + " OR ".join([f'{field} CONTAINS "{q}"' for q in queries]) + ")"
            if component["invert"]: as_filter = "NOT " + as_filter
            filters.append(as_filter)
        _search = " ".join(search)
        _filter = " AND ".join(filters)
        return _search,  dict(filter=_filter)



class SearchQueryHelper:

    @staticmethod
    def search_bar(s):
        """Creates a  search Query using a familiar search bar: ~title:bucket cast:"jack nicholson"""
        # NOTE: ~title:bucket cast:"jack nicholson" bruce
        # NOTE: ~ is NOT.
        # NOTE: AND is implied between fields. OR can be used with multiple phases to search into a field.
        # NOTE: a phase in quotes implies a direct match of that phrase: i.e., "jack nicholson" does not match "jack"
        # NOTE: all <field>: text next <field>: queries into field, i.e., search cast field for "jack nicholson" bruce
        # NOTE: multiple phrases within a <field>: implies OR: i.e., "phrase1" word2 => "phrase1" OR word2
        # (Q("match_phrase", cast='jack nicholson') | Q("match", cast='bruce')) & Q("bool", filter=[~Q("match", title="bucket")])
        clean = string.ascii_letters + string.digits + """ ~:.?!'" """
        s = "".join([c for c in s if c in clean])

        items = s.split(" ")

        # if the user does not use a field simply add __NOFIELD__:<original text query>
        is_field = [i for i, item in enumerate(items) if ":" in item]
        if len(is_field) == 0:  items[0] = f"__NOFIELD__:{items[0]}"

        # as normal
        is_field = [i for i, item in enumerate(items) if ":" in item] + [len(items)]  # makes next line one line
        items = [" ".join(items[is_field[i]:is_field[i+1]]) for i in range(len(is_field)-1)]
        components = []
        for i, item in enumerate(items):
            q = item.split(":")  # e.g., ~title:bucket ==> is_not=True, q_key=title
            qfield, qvalue = q[0], ":".join(q[1:])
            is_not = qfield.startswith("~")
            field = qfield[1:] if is_not else qfield  # ~title => title   or title => title
            field = None if field == "__NOFIELD__" else field.lower()

            pattern = '"([^"]*)"'
            quoted_strings = [g.group(1) for g in re.finditer(pattern, qvalue)]
            non_quoted_strings = [p.strip() for p in re.sub(pattern, "", qvalue).split(" ") if p.strip() != ""]
            ops = []
            for qs in quoted_strings: ops.append(dict(quoted=True, s=qs))
            for qs in non_quoted_strings: ops.append(dict(quoted=False, s=qs))
            components.append(dict(invert=is_not, ops=ops, field=field))
        return components

