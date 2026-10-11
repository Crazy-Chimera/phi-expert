# Φ-Expert

Modulární API služba postavená na FastAPI. Projekt obsahuje katalog reprezentativních formulí modelu Φ, numerické pomocné funkce, jednoduchou JSON paměť, klasifikaci dotazů, prompt builder a základní metriky.

> **Epistemická poznámka:** katalog je pracovní zápis dodaného teoretického modelu, nikoli vědecký konsenzus. Výpočet podle formule nepotvrzuje fyzikální platnost modelu.

## Lokální spuštění

Vyžaduje Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

API dokumentace: `/docs`; veřejná kontrola zdraví: `/health`.

## Endpointy

| Metoda | Cesta | Účel | Přístup |
|---|---|---|---|
| GET, HEAD | `/` | Základní informace o službě | veřejný |
| GET | `/health` | Health check | veřejný |
| POST | `/ask` | Dotaz na nakonfigurovaného LLM poskytovatele | token |
| GET, POST | `/profile` | Čtení a aktualizace profilu uživatele | token |
| GET, DELETE | `/memory` | Čtení nebo mazání historie | token |
| GET | `/metrics` | Základní provozní metriky | token |
| GET | `/formulas` | Katalog formulí a počet položek | token |
| GET | `/formulas/{category}` | Formule kategorie A až O | token |
| POST | `/compute` | Numerické výpočty podporovaných operací | token |

Chráněné endpointy vyžadují hlavičku `Authorization: Bearer <PHI_API_TOKEN>`. Pokud token není nastaven, chráněné endpointy vracejí HTTP 503; při chybném nebo chybějícím tokenu vracejí HTTP 401.

### Příklad

```bash
curl https://phi-expert.onrender.com/health
curl -H "Authorization: Bearer $PHI_API_TOKEN" \
  https://phi-expert.onrender.com/formulas
curl -X POST -H "Authorization: Bearer $PHI_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"operation":"elegance","parameters":{"C":2,"K":0.5}}' \
  https://phi-expert.onrender.com/compute
```

Podporované operace `/compute`: `phi`, `distance`, `elegance`, `mass`, `information_force`, `action`.

## Konfigurace

- `PHI_API_TOKEN` — povinný pro chráněné endpointy.
- `PHI_API_BASE_URL`, `PHI_API_KEY`, `PHI_MODEL` — všechny tři jsou potřeba pro generování přes OpenAI-kompatibilní API.
- `PHI_DATA_DIR` — adresář JSON paměti; výchozí `/tmp/phi-expert-data`.

Bez konfigurace modelového poskytovatele endpoint `/ask` vrátí HTTP 503 s vysvětlením. Do veřejného repozitáře nikdy neukládejte API klíče ani produkční tokeny.

## Paměť a limity

Paměť je JSON soubor určený pro jednu instanci. Výchozí cesta v `/tmp` není trvalé úložiště; data mohou po restartu zmizet. Toto řešení není vhodné pro více instancí ani souběžný produkční provoz. Pro trvalou paměť použijte persistentní disk nebo externí databázi a promyslete ochranu osobních údajů.

Metriky jsou vedené v paměti procesu a po restartu se resetují. Katalog nyní obsahuje reprezentativní základní položky pro kategorie A–O; nejde o úplnou rekonstrukci všech dříve navržených formulí.

## Testy

```bash
pip install pytest
pytest -q
```

## Nasazení na Render

Repozitář je propojen s Renderem. Konfigurace je popsána v `render.yaml` (build: `pip install -r requirements.txt`, start: `uvicorn app:app --host 0.0.0.0 --port $PORT`, health check: `/health`). Tajné proměnné nastavujte v dashboardu Renderu, nikoli v repozitáři.
