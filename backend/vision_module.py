import os
from pathlib import Path
from typing import Optional

import httpx

OLLAMA_HOST = "http://127.0.0.1:11434"
VISION_MODEL = "llava-mini"


class VisionModule:
    """Optional vision support for screen understanding via a local Ollama vision model."""

    def __init__(self, model: str = VISION_MODEL, endpoint: str = OLLAMA_HOST):
        self.model = model
        self.endpoint = endpoint

    async def describe_screen(self, image_path: str, prompt: str) -> str:
        if not Path(image_path).exists():
            return "Screenshot file not found."

        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                files = {
                    "image": (Path(image_path).name, image_bytes, "image/png"),
                }
                data = {"model": self.model, "prompt": prompt}
                response = await client.post(
                    f"{self.endpoint}/vision",
                    data=data,
                    files=files,
                )
                response.raise_for_status()
                result = response.json()
                return self._extract_text(result)
        except Exception as exc:
            return f"Vision module failed: {exc}"

    def _extract_text(self, payload: dict) -> str:
        if isinstance(payload, dict):
            if "completion" in payload:
                return str(payload["completion"]) or ""
            if "choices" in payload and payload["choices"]:
                first = payload["choices"][0]
                if isinstance(first, dict):
                    if "message" in first and isinstance(first["message"], dict):
                        return str(first["message"].get("content", ""))
                    return str(first.get("content", ""))
            if "output" in payload:
                return str(payload["output"])
        return str(payload)
