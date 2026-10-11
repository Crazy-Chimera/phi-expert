"""Φ-Expert API service."""
from __future__ import annotations

import os
from pathlib import Path
from threading import RLock
from typing import Any

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

load_dotenv()

APP_NAME = "Φ-Expert"
DATA_DIR = Path(os.getenv("PHI_DATA_DIR", "/tmp/phi-expert-data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
MEMORY_FILE = DATA_DIR / "memory.json"
_lock = RLock()

app = FastAPI(title=APP_NAME, version="1.0.0", description="Modulární API pro Φ-Expert.")


def authorize(authorization: str | None = Header(default=None)) -> None:
    token = os.getenv("PHI_API_TOKEN", "").strip()
    if not token:
        return
    if authorization != f"Bearer {token}":
        raise HTTPException(status_code=401, detail="Neplatný nebo chybějící API token.")


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=12000)
    context: dict[str, Any] = Field(default_factory=dict)


class ProfileRequest(BaseModel):
    profile: dict[str, Any] = Field(default_factory=dict)


def read_memory() -> list[dict[str, Any]]:
    import json
    with _lock:
        if not MEMORY_FILE.exists():
            return []
        try:
            value = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
            return value if isinstance(value, list) else []
        except (OSError, ValueError):
            return []


def write_memory(items: list[dict[str, Any]]) -> None:
    import json
    with _lock:
        tmp = MEMORY_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(MEMORY_FILE)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": APP_NAME}


@app.get("/")
def root() -> dict[str, str]:
    return {"service": APP_NAME, "docs": "/docs", "health": "/health"}


@app.post("/ask", dependencies=[Depends(authorize)])
def ask(payload: AskRequest) -> dict[str, Any]:
    """Return a transparent baseline response; connect a model provider to enable generation."""
    base_url = os.getenv("PHI_API_BASE_URL", "").strip()
    api_key = os.getenv("PHI_API_KEY", "").strip()
    model = os.getenv("PHI_MODEL", "").strip()
    if base_url and api_key and model:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url=base_url)
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Jsi asistent Φ-Expert. Odděluj hypotézy od ověřených faktů a nevydávej spekulativní tvrzení za vědecky potvrzená."},
                    {"role": "user", "content": payload.question},
                ],
            )
            answer = response.choices[0].message.content or ""
            return {"answer": answer, "model": model, "mode": "provider"}
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Poskytovatel modelu selhal: {type(exc).__name__}") from exc
    return {
        "answer": "Φ-Expert API je dostupné, ale generování odpovědí není nakonfigurováno. Nastavte PHI_API_BASE_URL, PHI_API_KEY a PHI_MODEL.",
        "mode": "configuration_required",
        "question": payload.question,
        "context": payload.context,
    }


@app.get("/profile", dependencies=[Depends(authorize)])
def get_profile() -> dict[str, Any]:
    return {"profile": read_memory()[:1]}


@app.post("/profile", dependencies=[Depends(authorize)])
def set_profile(payload: ProfileRequest) -> dict[str, Any]:
    write_memory([{"profile": payload.profile}])
    return {"status": "saved", "profile": payload.profile}


@app.get("/memory", dependencies=[Depends(authorize)])
def get_memory() -> dict[str, Any]:
    return {"items": read_memory()}


@app.post("/memory", dependencies=[Depends(authorize)])
def add_memory(item: dict[str, Any]) -> dict[str, Any]:
    items = read_memory()
    items.append(item)
    write_memory(items)
    return {"status": "saved", "count": len(items)}


@app.delete("/memory", dependencies=[Depends(authorize)])
def clear_memory() -> dict[str, str]:
    write_memory([])
    return {"status": "cleared"}


@app.get("/metrics", dependencies=[Depends(authorize)])
def metrics() -> dict[str, Any]:
    return {"service": APP_NAME, "version": app.version, "memory_items": len(read_memory())}


@app.get("/formulas", dependencies=[Depends(authorize)])
def formulas() -> dict[str, Any]:
    return {
        "categories": [],
        "note": "Katalog formul není v této základní deploy verzi připojen.",
    }
