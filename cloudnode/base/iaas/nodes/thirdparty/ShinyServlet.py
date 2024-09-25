import shiny
import threading
import abc


class ServletShiny(abc.ABC):
    provider = "shiny"

    def __init__(self, hostport):
        self.protocol = "http://"
        self.hostport = hostport
        self.app = None
        self.thread = None

    @staticmethod
    @abc.abstractmethod
    def ui(request): pass

    @staticmethod
    @abc.abstractmethod
    def server(input, output, session): pass

    def start(self):
        if self.app is not None: raise RuntimeError("ServletShiny.app is not None. Was this run already?")
        self.app = shiny.App(self.ui, self.server)
        (host, port), ui = self.hostport.split(":"), f"{self.protocol}{self.hostport}"
        self.thread = threading.Thread(target=self.app.run, kwargs=dict(host=host, port=int(port)), name=f"servlet={ui}", daemon=True)
        self.thread.start()
        # does not add to endpoints file because we know this is a ui
