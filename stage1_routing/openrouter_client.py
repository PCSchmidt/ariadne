"""Hardened OpenRouter client for the Stage 1 routing matrix.

Adds (vs the thesis-slice client): explicit max_tokens, UTF-8 safety, and the
caller-side JSON-repair retry lives in matrix_runner. Parses cost + cached tokens.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

import httpx

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


@dataclass
class LLMCall:
    model: str
    content: str
    input_tokens: int
    output_tokens: int
    cached_tokens: int
    cost_usd: float
    latency_s: float


class OpenRouterClient:
    def __init__(self, api_key: Optional[str] = None, timeout: float = 240.0,
                 app_title: str = "ariadne-stage1-routing"):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY not set (see .env.example).")
        self.app_title = app_title
        self._client = httpx.Client(timeout=timeout)

    def chat(self, model: str, messages: List[Dict[str, str]],
             session_id: Optional[str] = None, temperature: float = 0.0,
             json_mode: bool = True, max_tokens: int = 4096,
             max_retries: int = 3) -> LLMCall:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-Title": self.app_title,
            "Content-Type": "application/json",
        }
        if session_id:
            headers["x-session-id"] = session_id[:256]
        body: Dict = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "usage": {"include": True},
        }
        if json_mode:
            body["response_format"] = {"type": "json_object"}

        last_err: Optional[Exception] = None
        for attempt in range(max_retries):
            t0 = time.time()
            try:
                resp = self._client.post(OPENROUTER_URL, headers=headers, json=body)
                resp.raise_for_status()
                data = resp.json()
                latency = time.time() - t0
                msg = data["choices"][0]["message"].get("content") or ""
                usage = data.get("usage", {}) or {}
                details = usage.get("prompt_tokens_details", {}) or {}
                return LLMCall(
                    model=model,
                    content=msg,
                    input_tokens=int(usage.get("prompt_tokens", 0) or 0),
                    output_tokens=int(usage.get("completion_tokens", 0) or 0),
                    cached_tokens=int(details.get("cached_tokens", 0) or 0),
                    cost_usd=float(usage.get("cost", 0.0) or 0.0),
                    latency_s=latency,
                )
            except Exception as e:  # noqa: BLE001
                last_err = e
                time.sleep(1.5 * (attempt + 1))
        raise RuntimeError(f"OpenRouter call to {model} failed after "
                           f"{max_retries} retries: {last_err}")

    def close(self):
        self._client.close()
