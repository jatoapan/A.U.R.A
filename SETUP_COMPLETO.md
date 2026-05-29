# 🚀 A.U.R.A - Setup Completo (Backend + Frontend)

Sistema de detección de fraude en siniestros con **FastAPI** (Backend) + **React** (Frontend).

## 📋 Requisitos previos

- Python 3.10+
- Node.js 18+ (para React)
- Cuenta Supabase con schema aplicado
- `.env` configurado en la raíz

## ⚡ Inicio Rápido (3 pasos)

### 1. Entrenar modelos (UNA sola vez)

```bash
# Terminal 1 - Raíz del proyecto
python scripts/export_supabase_to_csv.py
python scripts/train_fraud_model.py
python scripts/run_scoring.py
```

✅ Confirmar que se crean `fraud_lr.joblib`, `fraud_iso.joblib` en `data/processed/`

### 2. Arrancar Backend (FastAPI)

```bash
# Terminal 2 - Raíz del proyecto
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

✅ Ver en http://localhost:8000/docs (Swagger UI)  
✅ Health check: http://localhost:8000/health

### 3. Arrancar Frontend (React)

```bash
# Terminal 3 - Carpeta frontend/
cd frontend
npm install  # Primera vez
npm run dev
```

✅ Abre http://localhost:3000

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend React (puerto 3000)                               │
│  - Listado de siniestros                                    │
│  - Detalle y análisis de riesgo                             │
│  - Chat conversacional                                      │
└───────────────────┬─────────────────────────────────────────┘
                    │ HTTP JSON (CORS)
┌───────────────────▼─────────────────────────────────────────┐
│  Backend FastAPI (puerto 8000)                              │
│  - GET /siniestros (listar)                                 │
│  - GET /siniestros/{id} (detalle)                           │
│  - POST /siniestros/{id}/score (calcular riesgo)            │
│  - POST /siniestros/{id}/chat (agente LLM)                  │
│  - POST /siniestros/score-all (batch)                       │
└───────────────────┬─────────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────────┐
│  Motor Python - Scoring Híbrido (SIN CAMBIOS)               │
│  - src/app/scoring.py (pipeline)                            │
│  - src/rules/ (reglas de negocio) → 70 pts                  │
│  - src/models/fraud_model.py (ML) → 20 pts                  │
│  - src/models/anomaly_model.py (anomalías) → 10 pts         │
│  - src/nlp/ (narrativa) → alimenta reglas                   │
└───────────────────┬─────────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────────┐
│  Supabase PostgreSQL                                        │
│  - siniestros (score_riesgo, semaforo_alerta, explicacion)  │
│  - polizas, proveedores, documentos                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Configuración (`.env` en raíz)

```env
# Supabase
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=eyJ...

# Chat LLM (opcional - TODO implementar)
OPENAI_API_KEY=sk-...
```

---

## 📚 Estructura de carpetas

```
A.U.R.A/
├── src/
│   ├── api/                  ← ⭐ NUEVO Backend FastAPI
│   │   ├── main.py
│   │   ├── schemas.py
│   │   ├── deps.py
│   │   ├── services/
│   │   │   ├── scoring_service.py
│   │   │   └── __init__.py
│   │   └── routers/
│   │       ├── health.py
│   │       ├── siniestros.py
│   │       ├── chat.py
│   │       └── __init__.py
│   ├── app/
│   │   └── scoring.py        ← Motor (no tocar)
│   ├── rules/                ← Reglas (no tocar)
│   ├── models/               ← ML (no tocar)
│   ├── nlp/                  ← NLP (no tocar)
│   ├── features/             ← Features (no tocar)
│   └── ...
├── frontend/                 ← ⭐ NUEVO Frontend React
│   ├── src/
│   │   ├── pages/
│   │   │   ├── ListadoSiniestros.jsx
│   │   │   └── DetalleSiniestro.jsx
│   │   ├── components/
│   │   │   ├── Navbar.jsx
│   │   │   ├── SemaforoIndicador.jsx
│   │   │   └── ScoreBar.jsx
│   │   ├── api/
│   │   │   └── client.js
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
├── data/processed/           ← Modelos entrenados
│   ├── fraud_lr.joblib
│   ├── fraud_iso.joblib
│   └── fraud_model_config.json
├── scripts/
│   ├── train_fraud_model.py
│   ├── run_scoring.py
│   └── ...
└── ...
```

---

## 🧪 Testing

### Backend
```bash
# Health check
curl http://localhost:8000/health

# Listar siniestros
curl "http://localhost:8000/siniestros?semaforo=ROJO&limit=5"

# Detalle
curl http://localhost:8000/siniestros/sin-e06928a9

# Score individual
curl -X POST http://localhost:8000/siniestros/sin-e06928a9/score
```

### Frontend
- Abre http://localhost:3000
- Verifica que se cargue el listado
- Click en "Ver detalle" para abrir detalle + chat

---

## ❌ Problemas comunes

### "Modelos no cargados"
```
Solución: python scripts/train_fraud_model.py
```

### "No se conecta con Supabase"
```
Solución: Verificar SUPABASE_URL y SUPABASE_KEY en .env
```

### "CORS error en el frontend"
```
Solución: Backend tiene CORS habilitado por defecto para desarrollo.
En prod, editar main.py: allow_origins=["https://tudominio.com"]
```

### "npm: comando no encontrado"
```
Solución: Instalar Node.js desde nodejs.org
```

---

## 🚀 Próximos pasos

### Backend
- [ ] Implementar agente LLM con OpenAI API (`src/api/routers/chat.py`)
- [ ] Agregar autenticación / autorizacion
- [ ] Persistencia mejorada de scores en batch
- [ ] Logging y monitoring

### Frontend
- [ ] Dashboard con gráficos por semáforo
- [ ] Exportar a CSV
- [ ] Filtros avanzados
- [ ] Tema oscuro

---

## 📖 Documentación

- [GUIA_BACK_FRONT.md](./GUIA_BACK_FRONT.md) - Guía técnica completa
- [docs/uso_ia.md](./docs/uso_ia.md) - Detalle del motor ML
- [docs/reglas_negocio.md](./docs/reglas_negocio.md) - Reglas de negocio
- [docs/arquitectura.md](./docs/arquitectura.md) - Arquitectura del sistema

---

## 👥 Equipo

**Backend:** FastAPI + Supabase  
**Frontend:** React + Vite + Tailwind CSS  
**Motor:** Python + scikit-learn + transformers

¡Listo para desarrollar! 🎉
