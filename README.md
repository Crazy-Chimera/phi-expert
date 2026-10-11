# Φ-Expert

Základní deployovatelná služba Φ-Expert postavená na FastAPI.

## Spuštění lokálně

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

Dokumentace API: `/docs`; kontrola zdraví: `/health`.

## Endpointy

- `GET /` — základní informace
- `GET /health` — health check
- `POST /ask` — základní odpověď nebo volání kompatibilního modelového API
- `GET/POST /profile` — načtení/uložení profilu
- `GET/POST/DELETE /memory` — práce s pamětí
- `GET /metrics` — základní provozní údaje
- `GET /formulas` — stav katalogu formulí

## Konfigurace

Proměnné prostředí: `PHI_API_TOKEN`, `PHI_API_BASE_URL`, `PHI_API_KEY`, `PHI_MODEL`, `PHI_DATA_DIR`.

Pokud je `PHI_API_TOKEN` nastaven, chrání API endpointy hlavičkou `Authorization: Bearer <token>`. Bez něj nejsou tyto endpointy autentizované; pro veřejný provoz token nastavte.

Modelové generování vyžaduje kompatibilního poskytovatele a všechny tři proměnné `PHI_API_BASE_URL`, `PHI_API_KEY` a `PHI_MODEL`. Bez nich `/ask` vrací informaci o chybějící konfiguraci.

Paměť se ukládá do JSON souboru. Cesta `/tmp` není trvalé úložiště a JSON úložiště není vhodné pro více instancí nebo souběžný produkční provoz. Pro trvalé nasazení nastavte persistentní disk nebo externí databázi.

## Nasazení na Render

Repozitář propojte s Renderem nebo použijte `render.yaml`. Build příkaz je `pip install -r requirements.txt`, start příkaz `uvicorn app:app --host 0.0.0.0 --port $PORT`. Nastavte `PHI_API_TOKEN` jako tajnou proměnnou v Renderu.

Poznámka: tato verze poskytuje deployovatelný základ API; katalog formulí a plná logika teoretického modelu nejsou v této základní revizi implementovány. Hypotézy Φ-Theory je nutné odlišovat od vědecky ověřených poznatků.
