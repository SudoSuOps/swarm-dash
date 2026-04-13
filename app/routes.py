from pathlib import Path

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates

from app.config import DEFAULT_MODEL, RECEIPTS_DIR, RUNS_DIR, OLLAMA_BASE_URL, UPLOADS_DIR
from app.file_extract import extract_pdf_text
from app.ollama_client import generate
from app.prompts import SYSTEM_PROMPTS
from app.schemas import Receipt
from app.storage import append_jsonl, ensure_dirs, write_json
from app.utils import new_id

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def list_recent_receipts(limit: int = 10):
    files = sorted(RECEIPTS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return [p.name for p in files[:limit]]

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    ensure_dirs()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "default_model": DEFAULT_MODEL,
            "recent_receipts": list_recent_receipts(),
            "response_text": "",
            "selected_mode": "chat",
            "selected_model": DEFAULT_MODEL,
            "last_receipt": None,
            "ollama_base_url": OLLAMA_BASE_URL,
        },
    )

@router.post("/run", response_class=HTMLResponse)
async def run_prompt(
    request: Request,
    prompt: str = Form(...),
    mode: str = Form("chat"),
    model: str = Form(DEFAULT_MODEL),
    document: UploadFile | None = File(None),
):
    ensure_dirs()
    run_id = new_id()
    run_trace = RUNS_DIR / f"{run_id}.jsonl"

    append_jsonl(run_trace, {
        "event": "run_started",
        "run_id": run_id,
        "mode": mode,
        "model": model,
        "prompt": prompt,
    })

    system_prompt = SYSTEM_PROMPTS.get(mode, SYSTEM_PROMPTS["chat"])
    append_jsonl(run_trace, {
        "event": "prompt_prepared",
        "run_id": run_id,
        "system_prompt": system_prompt,
    })

    uploaded_filename = None
    uploaded_file_path = None
    extracted_chars = None
    full_prompt = prompt

    if document and document.filename:
        uploaded_filename = document.filename
        safe_name = Path(document.filename).name
        save_path = UPLOADS_DIR / f"{run_id}_{safe_name}"
        file_bytes = await document.read()
        save_path.write_bytes(file_bytes)
        uploaded_file_path = str(save_path)

        append_jsonl(run_trace, {
            "event": "file_uploaded",
            "run_id": run_id,
            "filename": uploaded_filename,
            "path": uploaded_file_path,
            "bytes": len(file_bytes),
        })

        try:
            extracted_text = extract_pdf_text(save_path)
            extracted_chars = len(extracted_text)

            append_jsonl(run_trace, {
                "event": "pdf_extracted",
                "run_id": run_id,
                "filename": uploaded_filename,
                "extracted_chars": extracted_chars,
            })

            if extracted_text.strip():
                full_prompt = (
                    "[DOCUMENT CONTEXT BEGIN]\n"
                    f"filename: {uploaded_filename}\n"
                    f"extracted_chars: {extracted_chars}\n\n"
                    f"{extracted_text}\n"
                    "[DOCUMENT CONTEXT END]\n\n"
                    f"{prompt}"
                )
                append_jsonl(run_trace, {
                    "event": "document_context_attached",
                    "run_id": run_id,
                    "filename": uploaded_filename,
                })
        except Exception as e:
            append_jsonl(run_trace, {
                "event": "pdf_extraction_failed",
                "run_id": run_id,
                "filename": uploaded_filename,
                "error": str(e),
            })

    status = "success"
    response_text = ""

    try:
        append_jsonl(run_trace, {
            "event": "ollama_request_started",
            "run_id": run_id,
            "model": model,
        })

        response_text = await generate(model=model, system=system_prompt, prompt=full_prompt)

        append_jsonl(run_trace, {
            "event": "ollama_response_received",
            "run_id": run_id,
            "response_preview": response_text[:300],
        })
    except Exception as e:
        status = "failed"
        response_text = f"Ollama request failed: {e}"
        append_jsonl(run_trace, {
            "event": "run_failed",
            "run_id": run_id,
            "error": str(e),
        })

    receipt = Receipt(
        receipt_id=run_id,
        model=model,
        mode=mode,
        prompt=prompt,
        status=status,
        response_preview=response_text[:500],
        uploaded_filename=uploaded_filename,
        uploaded_file_path=uploaded_file_path,
        extracted_chars=extracted_chars,
        artifacts=[str(run_trace)] + ([uploaded_file_path] if uploaded_file_path else []),
    )
    receipt_path = RECEIPTS_DIR / f"{run_id}.json"
    write_json(receipt_path, receipt.model_dump())

    append_jsonl(run_trace, {
        "event": "receipt_written",
        "run_id": run_id,
        "receipt_path": str(receipt_path),
    })
    append_jsonl(run_trace, {
        "event": "run_completed" if status == "success" else "run_finished_with_error",
        "run_id": run_id,
        "status": status,
    })

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "default_model": DEFAULT_MODEL,
            "recent_receipts": list_recent_receipts(),
            "response_text": response_text,
            "selected_mode": mode,
            "selected_model": model,
            "last_receipt": receipt,
            "ollama_base_url": OLLAMA_BASE_URL,
        },
    )

@router.get("/receipt/{receipt_id}", response_class=PlainTextResponse)
async def get_receipt(receipt_id: str):
    path = RECEIPTS_DIR / f"{receipt_id}.json"
    if not path.exists():
        return PlainTextResponse("receipt not found", status_code=404)
    return PlainTextResponse(path.read_text(encoding="utf-8"))

@router.get("/trace/{receipt_id}", response_class=PlainTextResponse)
async def get_trace(receipt_id: str):
    path = RUNS_DIR / f"{receipt_id}.jsonl"
    if not path.exists():
        return PlainTextResponse("trace not found", status_code=404)
    return PlainTextResponse(path.read_text(encoding="utf-8"))

@router.get("/health", response_class=PlainTextResponse)
async def health():
    return PlainTextResponse("ok")
