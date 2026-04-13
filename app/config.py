from pathlib import Path

OLLAMA_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "gemma4:latest"
DATA_DIR = Path("data")
RECEIPTS_DIR = DATA_DIR / "receipts"
RUNS_DIR = DATA_DIR / "runs"
LOGS_DIR = DATA_DIR / "logs"
UPLOADS_DIR = DATA_DIR / "uploads"
