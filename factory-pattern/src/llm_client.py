import time

from config_loader import ConfigLoader
from llm_factory import LLMFactory


def main():

    prompt = "Who is Elon Musk?"

    # read provider from configuration
    provider = ConfigLoader.get("provider")

    factory = LLMFactory.instance()

    print(f"\n*** PROVIDER: {provider.upper()} ***")

    try:

        llm = factory.create(provider, prompt)

        start = time.time()

        response = llm.process()

        elapsed = time.time() - start

        print(response.content if hasattr(response, "content") else response)

        print(f"\nExecution time: {elapsed:.2f} seconds")

    except Exception as exc:

        print(f"{provider} failed: {exc}")


if __name__ == "__main__":
    main()