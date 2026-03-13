####################################################
# LLM Factory
# Author: Ravi Natarajan
####################################################

from threading import Lock

from llm_server import OllamaServer, OpenAIServer


class LLMFactory:
    _instance = None
    _lock = Lock()

    def __init__(self):
        self._registry = {}
        self._bootstrapped = False

    @classmethod
    def instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def bootstrap(self):
        if self._bootstrapped:
            return

        self.register("Ollama", OllamaServer)
        #self.register("Watsonx", WatsonxServer)
        self.register("OpenAI", OpenAIServer)

        self._bootstrapped = True

    def register(self, name, cls):
        self._registry[name] = cls

    def create(self, name, prompt):
        if not self._bootstrapped:
            self.bootstrap()

        if name not in self._registry:
            raise ValueError(f"Unknown LLM server type: {name}")

        return self._registry[name](prompt)