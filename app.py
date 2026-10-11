"""Φ-Expert API service."""
from __future__ import annotations
import os
from pathlib import Path
from typing import Any
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from phi_formulas import FORMULA_CATEGORIES, compute_action, compute_distance, compute_elegance, compute_F_info, compute_mass, compute_phi, get_formula_catalog
from phi_memory import JsonMemory
from phi_metrics import record_request, snapshot
from phi_prompt import build_system_prompt
from phi_router import classify_question

load_dotenv()
APP_NAME = "Φ-Expert"
DATA_DIR = Path(os.getenv("PHI_DATA_DIR", "/tmp/phi-expert-data"))
memory = JsonMemory(DATA_DIR)
app = FastAPI(title=APP_NAME, version="1.1.0", description="Modulární API pro Φ-Expert.")

def authorize(authorization: str | None = Header(default=None)) -> None:
    token = os.getenv("PHI_API_TOKEN", "").strip()
    if not token:
        raise HTTPException(status_code=503, detail="API není zabezpečené. Nastavte PHI_API_TOKEN v prostředí.")
    if authorization != f"Bearer {token}":
        raise HTTPException(status_code=401, detail="Neplatný nebo chybějící API token.")

class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=12000)
    user_id: str = Field(default="default", min_length=1, max_length=128)
    context: dict[str, Any] = Field(default_factory=dict)

class ProfileRequest(BaseModel):
    user_id: str = Field(default="default", min_length=1, max_length=128)
    profile: dict[str, Any] = Field(default_factory=dict)

class ComputeRequest(BaseModel):
    operation: str
    parameters: dict[str, Any] = Field(default_factory=dict)

@app.get("/")
def root() -> dict[str, str]:
    return {"service": APP_NAME, "version": app.version, "docs": "/docs", "health": "/health"}

@app.head("/")
def root_head():
    return {}

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": APP_NAME, "version": app.version}

@app.post("/ask", dependencies=[Depends(authorize)])
async def ask(payload: AskRequest) -> dict[str, Any]:
    import time
    start = time.perf_counter()
    category = classify_question(payload.question)
    profile = await memory.get_profile(payload.user_id)
    base_url, api_key, model = (os.getenv(k, "").strip() for k in ("PHI_API_BASE_URL", "PHI_API_KEY", "PHI_MODEL"))
    if not (base_url and api_key and model):
        raise HTTPException(status_code=503, detail="Generování není nakonfigurováno. Nastavte PHI_API_BASE_URL, PHI_API_KEY a PHI_MODEL.")
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url, timeout=45.0, max_retries=1)
        history = await memory.get_recent_conversations(payload.user_id, limit=6)
        messages = [{"role": "system", "content": build_system_prompt(category, profile)}]
        for item in history:
            messages.extend([{"role": "user", "content": item["question"]}, {"role": "assistant", "content": item["answer"]}])
        messages.append({"role": "user", "content": payload.question})
        response = client.chat.completions.create(model=model, messages=messages)
        answer = response.choices[0].message.content or ""
        await memory.add_conversation(payload.user_id, payload.question, answer, category)
        record_request("/ask", time.perf_counter() - start)
        return {"answer": answer, "model": model, "category": category, "mode": "provider"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Poskytovatel modelu selhal: {type(exc).__name__}") from exc

@app.get("/profile", dependencies=[Depends(authorize)])
async def get_profile(user_id: str = "default") -> dict[str, Any]:
    return {"user_id": user_id, "profile": await memory.get_profile(user_id)}

@app.post("/profile", dependencies=[Depends(authorize)])
async def set_profile(payload: ProfileRequest) -> dict[str, Any]:
    return {"status": "saved", "user_id": payload.user_id, "profile": await memory.update_profile(payload.user_id, payload.profile)}

@app.get("/memory", dependencies=[Depends(authorize)])
async def get_memory(user_id: str = "default", limit: int = 20) -> dict[str, Any]:
    if not 1 <= limit <= 100:
        raise HTTPException(status_code=422, detail="limit musí být v rozsahu 1–100.")
    return {"user_id": user_id, "items": await memory.get_recent_conversations(user_id, limit)}

@app.delete("/memory", dependencies=[Depends(authorize)])
async def clear_memory(user_id: str | None = None) -> dict[str, str]:
    await memory.clear(user_id)
    return {"status": "cleared", "scope": "all" if user_id is None else "user"}

@app.get("/metrics", dependencies=[Depends(authorize)])
def metrics() -> dict[str, Any]:
    return {"service": APP_NAME, "version": app.version, **snapshot()}

@app.get("/formulas", dependencies=[Depends(authorize)])
def formulas() -> dict[str, Any]:
    return {"categories": get_formula_catalog(), "count": sum(len(v) for v in FORMULA_CATEGORIES.values()),
            "epistemic_note": "Katalog popisuje dodaný teoretický model, nikoli vědecký konsenzus."}

@app.get("/formulas/{category}", dependencies=[Depends(authorize)])
def formula_category(category: str) -> dict[str, Any]:
    key = category.upper()
    if key not in FORMULA_CATEGORIES:
        raise HTTPException(status_code=404, detail="Kategorie musí být A až O.")
    return {"category": key, "formulas": FORMULA_CATEGORIES[key]}

@app.post("/compute", dependencies=[Depends(authorize)])
def compute(payload: ComputeRequest) -> dict[str, Any]:
    p = payload.parameters
    functions = {
        "phi": lambda: compute_phi(p["I_ij"], p.get("V_P", 1.616255e-35**3)),
        "distance": lambda: compute_distance(p["I_ij"]),
        "elegance": lambda: compute_elegance(p["C"], p["K"]),
        "mass": lambda: compute_mass(p["dC_dt"]),
        "information_force": lambda: compute_F_info(p["gamma"], p["grad_C"]),
        "action": lambda: compute_action(p["phi"], p["V"], p["C"], p["lambda_"]),
    }
    if payload.operation not in functions:
        raise HTTPException(status_code=400, detail={"message": "Neznámá operace.", "supported": sorted(functions)})
    try:
        value = functions[payload.operation]()
        if isinstance(value, float) and (value != value or value in (float("inf"), float("-inf"))):
            value = "Infinity" if value > 0 else "-Infinity"
        return {"operation": payload.operation, "result": value, "note": "Výsledek je výpočet zadaného modelu, ne potvrzení jeho fyzikální platnosti."}
    except KeyError as exc:
        raise HTTPException(status_code=422, detail=f"Chybí parametr: {exc.args[0]}") from exc
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
