import httpx

from app.config import OLLAMA_BASE_URL

async def generate(model: str, system: str, prompt: str) -> str:
    url = f"{OLLAMA_BASE_URL}/api/chat"
    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    }

    async with httpx.AsyncClient(timeout=300.0) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()

    message = data.get("message", {})
    content = message.get("content", "")
    return content or "[empty response]"
