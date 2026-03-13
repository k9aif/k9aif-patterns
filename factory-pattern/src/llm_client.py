############################################################
# LLM Client
# Demonstrates use of the LLMFactory
############################################################

import time
from llm_factory import LLMFactory


class LLMClient:

    def __init__(self, provider: str):
        self.provider = provider
        self.factory = LLMFactory.instance()

    def ask(self, prompt: str):

        llm = self.factory.create(self.provider, prompt)

        start_time = time.time()
        response = llm.process()
        execution_time = time.time() - start_time

        print(response)
        print(f"Execution time: {execution_time:.2f} seconds")

        return response


def main():

    prompt = "Who is Elon Musk?"

    for provider in ["Ollama"]:

        print(f"\n*** {provider.upper()} ***")

        try:
            client = LLMClient(provider)
            client.ask(prompt)

        except Exception as e:
            print(f"{provider} failed: {e}")


if __name__ == "__main__":
    main()