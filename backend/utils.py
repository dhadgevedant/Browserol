import json
import re
from datetime import datetime
from pathlib import Path

LOG_FILE = Path(__file__).resolve().parent.parent / "agent.log"


def init_logger() -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not LOG_FILE.exists():
        LOG_FILE.write_text("")


def save_log(entry: str) -> None:
    timestamp = datetime.utcnow().isoformat() + "Z"
    line = f"[{timestamp}] {entry}\n"
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(line)


def safe_parse_json(text: str):
    text = text.strip()
    if not text:
        raise ValueError("No text to parse from model output.")

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pattern = re.compile(r"(\[.*\])", re.S)
        match = pattern.search(text)
        if match:
            return json.loads(match.group(1))
        raise
