"""
LLM client that sends attack prompts to the TARGET application being audited.
Supports OpenAI-compatible APIs, Anthropic, and custom HTTP endpoints.
"""

import asyncio
from typing import Optional

import httpx

from backend.models.audit import TargetConfig
from backend.utils.logger import get_logger

logger = get_logger(__name__)

_DEFAULT_HEADERS = {"Content-Type": "application/json"}


class TargetLLMClient:
    """Sends probes to the LLM application under audit."""

    def __init__(self, config: TargetConfig):
        self.config = config
        self.provider = config.provider.lower()

    async def send(self, user_message: str, system_message: Optional[str] = None) -> str:
        """Send a message to the target LLM and return the response text."""
        try:
            if self.provider == "openai":
                return await self._send_openai(user_message, system_message)
            elif self.provider == "anthropic":
                return await self._send_anthropic(user_message, system_message)
            elif self.provider == "custom":
                return await self._send_custom(user_message, system_message)
            else:
                raise ValueError(f"Unknown provider: {self.provider}")
        except Exception as exc:
            logger.warning("Target LLM error: %s", exc)
            return f"[ERROR] {exc}"

    # ── OpenAI-compatible ──────────────────────────────────────────────────

    async def _send_openai(self, user_msg: str, system_msg: Optional[str]) -> str:
        base_url = self.config.url or "https://api.openai.com/v1"
        messages = []
        if system_msg:
            messages.append({"role": "system", "content": system_msg})
        messages.append({"role": "user", "content": user_msg})

        payload = {
            "model": self.config.model,
            "messages": messages,
            "max_tokens": 1024,
            "temperature": 0.7,
        }
        headers = {
            **_DEFAULT_HEADERS,
            "Authorization": f"Bearer {self.config.api_key}",
        }

        async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
            resp = await client.post(f"{base_url}/chat/completions", json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    # ── Anthropic ─────────────────────────────────────────────────────────

    async def _send_anthropic(self, user_msg: str, system_msg: Optional[str]) -> str:
        base_url = self.config.url or "https://api.anthropic.com"
        headers = {
            **_DEFAULT_HEADERS,
            "x-api-key": self.config.api_key,
            "anthropic-version": "2023-06-01",
        }
        payload: dict = {
            "model": self.config.model,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": user_msg}],
        }
        if system_msg:
            payload["system"] = system_msg

        async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
            resp = await client.post(f"{base_url}/v1/messages", json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"]

    # ── Custom HTTP endpoint ───────────────────────────────────────────────

    async def _send_custom(self, user_msg: str, system_msg: Optional[str]) -> str:
        """POST to a custom endpoint that accepts {message: str, system: str} → {response: str}."""
        if not self.config.url:
            raise ValueError("Custom provider requires a URL")

        headers = {
            **_DEFAULT_HEADERS,
            "Authorization": f"Bearer {self.config.api_key}",
        }
        payload = {"message": user_msg, "system": system_msg or "", "model": self.config.model}

        async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
            resp = await client.post(self.config.url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            # Flexible response field extraction
            return (
                data.get("response")
                or data.get("text")
                or data.get("content")
                or data.get("message")
                or str(data)
            )
