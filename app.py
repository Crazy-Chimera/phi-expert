"""Φ-Expert API service."""
from __future__ import annotations
import os
from pathlib import Path
from typing import Any
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from phi_formulas import FORMULA_CATEGORIES, PLANCK_VOLUME, compute_action, compute_distance, compute_elegance, compute_F_info, compute_mass, compute_phi, get_formula_catalog
from phi_memory import JsonMemory
from phi_metrics import record_request, snapshot
from phi_prompt import build_system_prompt
from phi_router import classify_question

load_dotenv()
APP_NAME = "Φ-Expert"
DATA_DIR = Path(os.getenv("PHI_DATA_DIR", "/tmp/phi-expert-data"))
memory = JsonMemory(DATA_DIR)
app = FastAPI(title=APP_NAME, version="1.1.0", description="Modulární API pro Φ-Expert.")
bearer_scheme = HTTPBearer(auto_error=False, scheme_name="HTTPBearer")

def authorize(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> None:
    token = os.getenv("PHI_API_TOKEN", "").strip()
    if not token:
        raise HTTPException(status_code=503, detail="API není zabezpečené. Nastavte PHI_API_TOKEN v prostředí.")
    if credentials is None or credentials.scheme.lower() != "bearer" or credentials.credentials != token:
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


@app.get("/auth", response_class=HTMLResponse, include_in_schema=False)
def auth_ui() -> str:
    """Dedicated browser UI for validating a bearer token and authorizing Swagger."""
    return """<!doctype html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Φ-Expert · API autorizace</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
  <style>
    :root { color-scheme: dark; --bg:#0b1020; --panel:#141c30; --line:#2a3854; --text:#edf3ff; --muted:#9baac5; --accent:#8ab4ff; }
    * { box-sizing:border-box; } body { margin:0; background:var(--bg); color:var(--text); font:16px/1.5 system-ui,-apple-system,sans-serif; }
    .shell { max-width:1080px; margin:36px auto; padding:0 18px; }
    .card { background:var(--panel); border:1px solid var(--line); border-radius:16px; padding:24px; box-shadow:0 18px 55px #0003; }
    h1 { margin:0 0 6px; font-size:clamp(24px,4vw,34px); } p { color:var(--muted); margin:8px 0 18px; }
    label { display:block; margin:14px 0 7px; font-weight:650; }
    input { width:100%; padding:13px 14px; color:var(--text); background:#080d19; border:1px solid var(--line); border-radius:9px; font:inherit; }
    .actions { display:flex; gap:10px; flex-wrap:wrap; margin-top:14px; }
    button,.link { border:0; border-radius:9px; padding:11px 16px; font:inherit; font-weight:700; cursor:pointer; text-decoration:none; }
    button { color:#081225; background:var(--accent); } .secondary { background:#263550; color:var(--text); }
    #status { min-height:26px; margin:14px 0 0; font-weight:650; } .hint { font-size:13px; }
    #swagger { margin-top:24px; background:#fff; border-radius:12px; overflow:hidden; }
    .swagger-ui .topbar { display:none; }
  </style>
</head>
<body><main class="shell">
  <section class="card">
    <h1>Φ-Expert · API autorizace</h1>
    <p>Vlož svůj <code>PHI_API_TOKEN</code> z Renderu. Token se ověří proti chráněnému endpointu a použije pouze v této stránce pro Swagger; neukládá se do localStorage.</p>
    <label for="token">Bearer token</label>
    <input id="token" type="password" autocomplete="off" spellcheck="false" placeholder="Vlož PHI_API_TOKEN">
    <div class="actions">
      <button id="apply">Ověřit token a autorizovat Swagger</button>
      <button class="secondary" id="clear" type="button">Vymazat token</button>
      <a class="link secondary" href="/docs">Otevřít běžný Swagger</a>
    </div>
    <div id="status" role="status" aria-live="polite"></div>
    <p class="hint">Nikdy sem nevkládej PHI_API_KEY (klíč poskytovatele modelu). Neposílej token nikomu dalšímu.</p>
  </section>
  <section id="swagger" aria-label="Swagger API"></section>
</main>
<script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script>
  const statusBox = document.getElementById('status');
  const tokenInput = document.getElementById('token');
  const ui = SwaggerUIBundle({
    url: '/openapi.json',
    dom_id: '#swagger',
    deepLinking: true,
    persistAuthorization: false,
    displayRequestDuration: true,
    presets: [SwaggerUIBundle.presets.apis],
    layout: 'BaseLayout'
  });
  document.getElementById('apply').addEventListener('click', async () => {
    const token = tokenInput.value.trim();
    if (!token) { statusBox.textContent = 'Vlož PHI_API_TOKEN.'; return; }
    statusBox.textContent = 'Ověřuji token…';
    try {
      const response = await fetch('/profile?user_id=auth-check', {
        headers: { 'Authorization': 'Bearer ' + token }
      });
      if (response.status === 401) { statusBox.textContent = 'Token je neplatný. Zkontroluj PHI_API_TOKEN v Renderu.'; return; }
      if (response.status === 503) { statusBox.textContent = 'Server nemá nastavený PHI_API_TOKEN. Zkontroluj Render Environment.'; return; }
      if (!response.ok) { statusBox.textContent = 'Ověření selhalo (HTTP ' + response.status + ').'; return; }
      ui.preauthorizeApiKey('HTTPBearer', token);
      statusBox.textContent = 'Token ověřen. Swagger je autorizován; rozbal endpoint a použij Try it out.';
    } catch (_) {
      statusBox.textContent = 'Nepodařilo se spojit se serverem. Zkus stránku obnovit.';
    }
  });
  document.getElementById('clear').addEventListener('click', () => {
    tokenInput.value = '';
    ui.authActions.logout(['HTTPBearer']);
    statusBox.textContent = 'Token vymazán z formuláře a Swagger autorizace zrušena.';
  });
</script>
</body></html>"""


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
        "phi": lambda: compute_phi(p["I_ij"], p.get("V_P", PLANCK_VOLUME)),
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
