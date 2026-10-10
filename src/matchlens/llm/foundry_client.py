"""LLM interface. NullClient = deterministic templates; FoundryClient = Microsoft Foundry (Azure OpenAI)."""
from __future__ import annotations

import logging
import os
from typing import Protocol

log = logging.getLogger("matchlens.llm")


class LLMClient(Protocol):
    def complete(self, system: str, prompt: str) -> str | None: ...


class NullClient:
    """No-op client: returning None makes agents use deterministic templates."""
    def complete(self, system: str, prompt: str) -> str | None:
        return None


class FoundryClient:
    """Calls a model deployed in Microsoft Foundry using your Azure login (no keys).

    Accepts either the Azure OpenAI endpoint (https://<res>.openai.azure.com/...)
    or the Foundry project endpoint (https://<res>.services.ai.azure.com/api/projects/<proj>).
    """
    def __init__(self, endpoint: str, model: str):
        from azure.identity import DefaultAzureCredential, get_bearer_token_provider
        from openai import OpenAI
        base = endpoint.rstrip("/")
        scope = ("https://cognitiveservices.azure.com/.default" if "openai.azure.com" in base
                 else "https://ai.azure.com/.default")
        if not base.endswith("/openai/v1"):
            base += "/openai/v1"
        token = get_bearer_token_provider(DefaultAzureCredential(), scope)
        self._client = OpenAI(base_url=base, api_key=token)
        self._model = model

    def complete(self, system: str, prompt: str) -> str | None:
        try:
            r = self._client.chat.completions.create(
                model=self._model, max_completion_tokens=300, timeout=10,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}])
            return (r.choices[0].message.content or "").strip() or None
        except Exception as exc:  # any LLM failure falls back to templates
            log.warning("Foundry call failed, using template: %s", exc)
            return None


def get_client() -> LLMClient:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    if os.getenv("USE_LLM", "false").lower() != "true":
        return NullClient()
    try:
        return FoundryClient(os.environ["FOUNDRY_ENDPOINT"], os.environ["FOUNDRY_MODEL"])
    except Exception as exc:
        log.warning("Foundry unavailable (%s); using templates", exc)
        return NullClient()