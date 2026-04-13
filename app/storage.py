import json
from pathlib import Path
from typing import Any

from app.config import RECEIPTS_DIR, RUNS_DIR, LOGS_DIR, UPLOADS_DIR

def ensure_dirs() -> None:
    for d in [RECEIPTS_DIR, RUNS_DIR, LOGS_DIR, UPLOADS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
