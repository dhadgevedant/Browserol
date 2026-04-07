import json
import re
from typing import Any, Dict, List

import httpx
from backend.utils import save_log

OLLAMA_HOST = "http://127.0.0.1:11434"
OLLAMA_MODEL = "qwen2.5:3b"
OLLAMA_PATH = "/api/generate"


def _strip_code_blocks(text: str) -> str:
    cleaned = re.sub(r"```(?:json\n)?(.+?)```", lambda m: m.group(1), text, flags=re.S)
    return cleaned.strip()


def _extract_json_array(text: str) -> str:
    trimmed = _strip_code_blocks(text).strip()
    if trimmed.startswith("[") and trimmed.endswith("]"):
        return trimmed

    start = trimmed.find("[")
    end = trimmed.rfind("]")
    if start != -1 and end != -1 and end > start:
        return trimmed[start : end + 1]

    raise ValueError("Could not extract JSON array from model output.")


def _parse_plan(text: str) -> List[Dict[str, Any]]:
    payload = _extract_json_array(text)
    plan = json.loads(payload)
    if not isinstance(plan, list):
        raise ValueError("LLM output must be a JSON array.")
    return plan


def _normalize_response(data: Any) -> str:
    if isinstance(data, dict):
        return str(data.get("response", "")).strip()
    return str(data).strip()


class OllamaLLM:
    """A lightweight interface to the local Ollama API."""

    def __init__(self, model: str = OLLAMA_MODEL, endpoint: str = OLLAMA_HOST):
        self.model = model
        self.endpoint = endpoint.rstrip("/")

    def _build_prompt(self, instruction: str) -> str:
        return f"""You are an AI agent that converts instructions into browser automation steps.
Return ONLY valid JSON. Do not explain.

Always include a click step when the instruction implies selecting or opening something (e.g., first result, video, product).

Examples:
- YouTube search: {{"action": "click", "selector": "ytd-video-renderer a#thumbnail"}}
- Google result: {{"action": "click", "selector": "h3"}}
- Amazon product: {{"action": "click", "selector": "div.s-main-slot a"}}

Full example:
[
{{"action": "open_url", "value": "https://youtube.com"}},
{{"action": "type", "selector": "input[name='search_query']", "value": "python tutorial"}},
{{"action": "press", "key": "Enter"}},
{{"action": "click", "selector": "ytd-video-renderer a#thumbnail"}}
]

Instruction: {instruction}
"""

    async def _call_ollama(self, instruction: str) -> str:
        payload = {
            "model": self.model,
            "prompt": self._build_prompt(instruction),
            "stream": False,
            "keep_alive": "5m"
        }

        timeout = httpx.Timeout(120.0, connect=10.0)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(f"{self.endpoint}{OLLAMA_PATH}", json=payload)
                response.raise_for_status()
                data = response.json()

        except httpx.ReadTimeout:
            save_log("Timeout occurred, retrying once...")
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(f"{self.endpoint}{OLLAMA_PATH}", json=payload)
                response.raise_for_status()
                data = response.json()

        save_log(f"Ollama raw response: {data}")
        return _normalize_response(data)

    async def generate_plan(self, instruction: str) -> List[Dict[str, Any]]:
        raw_text = await self._call_ollama(instruction)
        try:
            return _parse_plan(raw_text)
        except (ValueError, json.JSONDecodeError) as first_error:
            save_log(f"First parse failed, retrying: {first_error}")
            raw_text = await self._call_ollama(instruction)
            return _parse_plan(raw_text)
