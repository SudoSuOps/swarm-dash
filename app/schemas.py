from datetime import datetime, UTC
from pydantic import BaseModel, Field
from typing import List, Optional

class RunRequest(BaseModel):
    prompt: str
    mode: str = "chat"
    model: str = "gemma4:latest"

class Receipt(BaseModel):
    receipt_id: str
    model: str
    mode: str
    prompt: str
    status: str
    response_preview: str
    uploaded_filename: Optional[str] = None
    uploaded_file_path: Optional[str] = None
    extracted_chars: Optional[int] = None
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    artifacts: List[str] = Field(default_factory=list)
