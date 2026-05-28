# A.U.R.A — Alerta Unificada de Riesgo en Siniestros

Prototipo de detección de fraude para el hackathon **Aseguradora del Sur**: score híbrido (reglas + ML + anomalías + NLP en reglas), semáforo y explicación para el analista.

---

## ¿Eres back o front?

**Empieza aquí → [GUIA_BACK_FRONT.md](GUIA_BACK_FRONT.md)**

Esa guía está pensada para que la implementes **con o sin IA** (incluye arquitectura, contrato API, pantallas, agente LLM, SQL, plan de 3 días y prompts listos para Cursor/ChatGPT).

> **¿Es solo un modelo local?** No es un experimento suelto: los `.joblib` + `src/app/scoring.py` son el **motor de inferencia** que el back carga al arrancar y llama con `score_from_tables()`. Ver sección **0** de la guía. Prueba rápida: `python scripts/run_scoring.py`.

El motor de fraude en Python **ya está hecho**; tu trabajo es API + UI + chat.

---

## Inicio rápido (equipo de datos)

```bash
pip install -r requirements.txt
cp .env.example .env   # SUPABASE_URL, SUPABASE_KEY

python -m src.ingestion.load_data          # data sintética → Supabase
python scripts/export_supabase_to_csv.py
python scripts/train_fraud_model.py        # fraud_lr.joblib + config
python scripts/run_scoring.py              # siniestros_scored.csv
```

---

## Estructura del repo

| Ruta | Rol |
|------|-----|
| `src/app/scoring.py` | **Scoring híbrido** (usar desde el back) |
| `src/api/` | FastAPI (stub — extender según guía) |
| `src/agents/` | Agente LLM (implementar según guía) |
| `src/rules/`, `src/models/`, `src/nlp/` | Motor IA (no tocar desde el front) |
| `database_schema.sql` | Schema Supabase |
| `notebooks/` | EDA y experimentos |
| `docs/uso_ia.md` | Detalle de capas IA |

---

## Arquitectura IA (resumen)

| Capa | Módulo | En el score final |
|------|--------|-------------------|
| NLP | `src/nlp/` | Solo vía reglas (RF-07) |
| Reglas | `src/rules/fraud_rules.py` | Hasta 70 pts |
| ML | `src/models/fraud_model.py` | Hasta 20 pts |
| Anomalías | `src/models/anomaly_model.py` | Hasta 10 pts |

Parámetros prod: **C=0.1**, **threshold ML=0.7** → `data/processed/fraud_model_config.json`.

---

## Documentación

- **[GUIA_BACK_FRONT.md](GUIA_BACK_FRONT.md)** — integración back, front y agente
- **[docs/uso_ia.md](docs/uso_ia.md)** — capas de IA
- `database_schema.sql` — tablas y pgvector

---

## Scripts útiles

```bash
python scripts/run_ds_flow.py              # generar + export CSV
python scripts/train_fraud_model.py
python scripts/run_scoring.py
uvicorn src.api.main:app --reload --port 8000   # API (tras implementar routers)
```
