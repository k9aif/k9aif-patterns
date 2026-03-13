from abc import ABC, abstractmethod
from langchain_ollama.chat_models import ChatOllama
from config_loader import ConfigLoader


class LLMServer(ABC):

    def __init__(self, prompt: str):
        self.prompt = prompt

    @abstractmethod
    def process(self):
        raise NotImplementedError


class OllamaServer(LLMServer):

    def process(self):

        host = ConfigLoader.get("ollama", "host")
        model = ConfigLoader.get("ollama", "model")

        print(f"using model: {model}, at {host}")

        chat_model = ChatOllama(
            ollama_host=host,
            model=model
        )

        return chat_model.invoke(self.prompt)

"""
class WatsonxServer(LLMServer):
    def process(self):
        api_key = os.getenv("API_KEY")
        ibm_cloud_url = os.getenv("IBM_CLOUD_URL")
        project_id = os.getenv("PROJECT_ID")
        space_id = os.getenv("SPACE_ID")
        model_id = "ibm/granite-20b-code-instruct"

        parameters = {
            "decoding_method": "greedy",
            "max_new_tokens": 900,
            "repetition_penalty": 1,
        }

        model = Model(
            model_id=model_id,
            params=parameters,
            credentials={"url": ibm_cloud_url, "apikey": api_key},
            project_id=project_id,
            space_id=space_id,
        )

        print(f"using model: {model_id}, at {ibm_cloud_url}")
        response = model.generate_text(prompt=self.prompt, guardrails=False)
        return response

"""

class OpenAIServer(LLMServer):
    def process(self):
        api_key = os.getenv("OPENAI_API_KEY")
        client = OpenAIClient(api_key=api_key)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": self.prompt},
            ],
        )

        return response.choices[0].message.content

