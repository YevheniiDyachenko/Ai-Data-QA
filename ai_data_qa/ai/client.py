import os
from abc import ABC, abstractmethod
from typing import Optional
from openai import OpenAI
from anthropic import Anthropic

class AIClient(ABC):
    @abstractmethod
    def completion(self, prompt: str) -> str:
        pass

class OpenAIClient(AIClient):
    def __init__(self, model: str, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def completion(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

class AnthropicClient(AIClient):
    def __init__(self, model: str, api_key: str):
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def completion(self, prompt: str) -> str:
        message = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text

def get_ai_client(provider: str, model: str, api_key_env_var: str) -> AIClient:
    api_key = os.getenv(api_key_env_var)
    if not api_key:
        raise ValueError(f"API key not found in environment variable: {api_key_env_var}")

    if provider.lower() == "openai":
        return OpenAIClient(model, api_key)
    elif provider.lower() == "anthropic":
        return AnthropicClient(model, api_key)
    else:
        raise ValueError(f"Unsupported AI provider: {provider}")
