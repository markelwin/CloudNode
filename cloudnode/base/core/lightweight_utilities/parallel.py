from multiprocessing import pool
import time

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ParallelizePool(object):
    """Handles the creation and management of multiple threads or processes; you probably want to use ParallelClient."""

    def __init__(self, processes=10, use_threads=False):
        self.pool = pool.ThreadPool(processes=processes) if use_threads else pool.Pool(processes=processes)

    def starmap(self, function, arguments):
        if len(arguments) == 0: return []
        n_work = len(arguments)
        start_t = time.time()
        results = self.pool.starmap(function, arguments)
        end_t = time.time()
        logger.info(f"Parallel Complete: {n_work} items in {end_t-start_t:.4f}s; {(end_t-start_t)/n_work:.4f}s/item.")
        return results


class ParallelClient(object):

    @staticmethod
    def use_protected_function_call(map_func, on_error_value=None):
        def protected_function_call(*argv):
            try:
                return map_func(*argv)
            except Exception as e:
                logger.error("protected_function_call", exc_info=True)
                return on_error_value
        protected_function_call.__name__ = f"protected_function_call_of_{map_func.__name__}"
        return protected_function_call

    @staticmethod
    def mapreduce(map_func, args, reduce_func=None, processes=12, use_threads=True, protect_throws=False):
        if protect_throws: map_func = ParallelClient.use_protected_function_call(map_func)
        if len(args) == 0: return []
        # This method now supports args being a dictionary of named arguments, i.e., kwargs. The Threadpool.starmap does
        # not handle this case (and expects all arguments to be unnamed and in order, which then is unpacked using *arg)
        # The workaround is to wrap map_func into a new function that accepts one variable, the kwargs, and does its
        # unpacking into the original function. To simplify this we simply refactor the method here into the two cases.
        _map_func_to_use = map_func
        if isinstance(args[0], dict):  # wrap function and kwargs
            def _wrapped_for_kwargs(dct): return map_func(**dct)
            args = [[dct] for dct in args]
            _map_func_to_use = _wrapped_for_kwargs
        # normal operation with map_func=_wrapped_for_kwargs and new args is [ [dct1], [dct2], [dct3], ...]
        if len(args) == 1:
            results = [_map_func_to_use(*args[0])]
        else:
            pool = ParallelizePool(processes=processes, use_threads=use_threads)
            results = pool.starmap(_map_func_to_use, args)
        if reduce_func is not None: results = reduce_func(results)
        return results

    @staticmethod
    def heteromap(fargs, processes=12, use_threads=True, protect_throws=False):
        """Multithreaded processing except allows the primary function to be different; see Note."""
        # NOTE: fargs is a list of pairs: [[function1, kwargs1], [function2, kwargs2]...]
        def _internal(function, kwargs): return function(**kwargs)
        return ParallelClient.mapreduce(_internal, fargs, reduce_func=None, processes=processes,
                                        use_threads=use_threads, protect_throws=protect_throws)

    @staticmethod
    def split_successes_and_failures(results):
        failures = [i for i,r in enumerate(results) if r is None]
        successes = {i: r for i,r in enumerate(results) if r is not None}
        return successes, failures
