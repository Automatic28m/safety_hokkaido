"""Thin provider client used by node 03 only.

Node 03 is the single place that talks to the LLM provider. Node 07 formats
prompts and parses decisions but never performs network calls; node 03 hands
the formatted messages to this client and passes the raw text back to node 07.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger("travel_ai_agent")

DEFAULT_API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_TIMEOUT_SECONDS = 30.0

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


class LLMClientError(Exception):
    """Raised when the provider cannot produce a completion."""


class GroqChatClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: str = DEFAULT_API_URL,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        session: Optional[Any] = None,
    ):
        if api_key is None:
            try:
                from config import config

                api_key = getattr(config, "GROQ_API_KEY", "")
            except ImportError:
                api_key = ""
        self.api_key = api_key or ""
        self.api_url = api_url
        self.timeout = timeout
        self._session = session or requests

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def complete(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.0,
        max_tokens: int = 1000,
        json_mode: bool = False,
    ) -> str:
        if not self.is_configured:
            raise LLMClientError("GROQ_API_KEY is not configured")

        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        content = self._post(payload)
        if content is None and json_mode:
            # Some models reject response_format; retry once without it.
            payload.pop("response_format", None)
            content = self._post(payload)
        if content is None:
            raise LLMClientError("provider returned no usable completion")
        return content

    def _post(self, payload: Dict[str, Any]) -> Optional[str]:
        try:
            response = self._session.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.timeout,
            )
        except requests.exceptions.Timeout as exc:
            raise LLMClientError("provider request timed out") from exc
        except requests.exceptions.RequestException as exc:
            raise LLMClientError(f"provider request failed: {exc.__class__.__name__}") from exc

        status = getattr(response, "status_code", 0)
        if status == 400 and "response_format" in payload:
            logger.warning("provider rejected response_format; retrying without it")
            return None
        if status != 200:
            raise LLMClientError(f"provider returned HTTP {status}")

        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise LLMClientError("provider returned a malformed completion") from exc

        if not isinstance(content, str) or not content.strip():
            raise LLMClientError("provider returned an empty completion")
        return content


def extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    """Returns the first JSON object found in ``text`` or ``None``.

    Handles bare JSON, JSON wrapped in markdown fences and JSON surrounded by
    explanatory prose.
    """
    if not isinstance(text, str) or not text.strip():
        return None

    candidates = [text.strip()]
    for fenced in _FENCE_RE.findall(text):
        candidates.insert(0, fenced.strip())

    for candidate in candidates:
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start == -1 or end == -1 or end <= start:
            continue
        snippet = candidate[start : end + 1]
        try:
            parsed = json.loads(snippet)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None
