# 🏗️ ARQUITECTURA IMPLEMENTADA - A.U.R.A (Back + Front)

**Documento:** Guía técnica detallada de la arquitectura implementada  
**Fecha:** Mayo 29, 2026  
**Estado:** MVP completo (80%) - Falta integrar OpenAI para chat LLM  

---

## 📋 TABLA DE CONTENIDOS

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Cambios Implementados](#cambios-implementados)
3. [Arquitectura General](#arquitectura-general)
4. [Backend - Estructura y Flujo](#backend---estructura-y-flujo)
5. [Frontend - Estructura y Componentes](#frontend---estructura-y-componentes)
6. [Flujo de Datos End-to-End](#flujo-de-datos-end-to-end)
7. [Base de Datos (Supabase)](#base-de-datos-supabase)
8. [Detalles de Cada Archivo](#detalles-de-cada-archivo)
9. [Cómo Extender](#cómo-extender)

---

## 📊 RESUMEN EJECUTIVO

### ¿Qué se implementó?

**ANTES:**
- Solo motor Python de scoring (src/app, src/rules, src/models, src/nlp)
- API stub vacía (main.py)
- Ningún frontend

**DESPUÉS:**
- ✅ **Backend FastAPI completo** - 6 endpoints REST + integración Supabase
- ✅ **Frontend React completo** - 2 páginas + 3 componentes + sistema de chat
- ✅ **Flujo E2E** - Desde el frontend, calcular score, persistir en BD y mostrar resultados
- ⚠️ **Chat LLM** - Stub (falta OpenAI, ver TODO.md)

### Números

| Componente | Archivos | Líneas | Status |
|-----------|----------|--------|--------|
| Backend | 9 | ~800 | ✅ Funcional |
| Frontend | 10 | ~600 | ✅ Funcional |
| Config | 4 | ~100 | ✅ Funcional |
| **TOTAL** | **23** | **~1500** | **✅ MVP Completo** |

---

## 🔄 CAMBIOS IMPLEMENTADOS

### Backend (src/api/)

| Archivo | Nuevo | Propósito |
|---------|-------|----------|
| `main.py` | ✅ Reescrito | FastAPI app con lifespan (carga modelos al startup) |
| `schemas.py` | ✅ NUEVO | Modelos Pydantic para request/response |
| `deps.py` | ✅ NUEVO | Inyección de dependencias (cliente Supabase) |
| `services/__init__.py` | ✅ NUEVO | SupabaseRepository (acceso a datos) |
| `services/scoring_service.py` | ✅ NUEVO | ScoringService (wrapper del motor Python) |
| `routers/__init__.py` | ✅ NUEVO | Router health check |
| `routers/siniestros.py` | ✅ NUEVO | Endpoints GET/POST para siniestros |
| `routers/chat.py` | ✅ NUEVO | Endpoint POST para chat (stub) |

### Frontend (frontend/)

| Archivo | Nuevo | Propósito |
|---------|-------|----------|
| `package.json` | ✅ NUEVO | Dependencias npm |
| `vite.config.js` | ✅ NUEVO | Config Vite (dev server en puerto 3000) |
| `tailwind.config.js` | ✅ NUEVO | Config Tailwind CSS |
| `postcss.config.js` | ✅ NUEVO | Config PostCSS |
| `index.html` | ✅ NUEVO | HTML principal |
| `src/main.jsx` | ✅ NUEVO | Punto de entrada React |
| `src/App.jsx` | ✅ NUEVO | App principal con routing |
| `src/index.css` | ✅ NUEVO | Estilos globales + Tailwind |
| `src/api/client.js` | ✅ NUEVO | Cliente axios para comunicar con backend |
| `src/components/Navbar.jsx` | ✅ NUEVO | Barra de navegación |
| `src/components/SemaforoIndicador.jsx` | ✅ NUEVO | Badge con color (VERDE/AMARILLO/ROJO) |
| `src/components/ScoreBar.jsx` | ✅ NUEVO | Barra visual de score (0-100) |
| `src/pages/ListadoSiniestros.jsx` | ✅ NUEVO | Página con tabla de siniestros + filtros |
| `src/pages/DetalleSiniestro.jsx` | ✅ NUEVO | Página de detalle + análisis + chat |
| `.env.example` | ✅ NUEVO | Plantilla variables entorno |
| `.gitignore` | ✅ NUEVO | Excluir node_modules, dist, etc |

### Documentación

| Archivo | Nuevo | Propósito |
|---------|-------|----------|
| `SETUP_COMPLETO.md` | ✅ NUEVO | Guía de instalación y arranque |
| `TODO.md` | ✅ NUEVO | Tareas pendientes + código para LLM |
| `start.sh` | ✅ NUEVO | Script para arrancar todo (solo Linux/Mac) |
| `ARQUITECTURA_IMPLEMENTADA.md` | ✅ ESTE | Documentación detallada |

---

## 🏗️ ARQUITECTURA GENERAL

```
┌─────────────────────────────────────────────────────────────────┐
│                    USUARIO (Navegador)                          │
│                   http://localhost:3000                         │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP/JSON (CORS)
┌────────────────────────▼────────────────────────────────────────┐
│                                                                  │
│                   FRONTEND (React + Vite)                       │
│                   Puerto: 3000                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Pages:                                                   │  │
│  │  - ListadoSiniestros.jsx  (Tabla + Filtros)             │  │
│  │  - DetalleSiniestro.jsx   (Análisis + Chat)             │  │
│  │                                                          │  │
│  │ Components:                                              │  │
│  │  - Navbar                                                │  │
│  │  - SemaforoIndicador                                     │  │
│  │  - ScoreBar                                              │  │
│  │                                                          │  │
│  │ API Client:                                              │  │
│  │  - axios (src/api/client.js)                             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP/JSON
┌────────────────────────▼────────────────────────────────────────┐
│                                                                  │
│                   BACKEND (FastAPI)                             │
│                   Puerto: 8000                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Routers:                                                 │  │
│  │  GET  /health                → Health check             │  │
│  │  GET  /siniestros            → Listar (filtros)         │  │
│  │  GET  /siniestros/{id}       → Detalle                  │  │
│  │  POST /siniestros/{id}/score → Calcular + guardar       │  │
│  │  POST /siniestros/score-all  → Batch                    │  │
│  │  POST /siniestros/{id}/chat  → Chat (stub)              │  │
│  │                                                          │  │
│  │ Services:                                                │  │
│  │  - SupabaseRepository (fetch/update)                    │  │
│  │  - ScoringService (wrapper motor Python)                │  │
│  │                                                          │  │
│  │ Dependencies:                                            │  │
│  │  - SupabaseClient (singleton)                            │  │
│  │  - Schemas Pydantic (validación)                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└────────────────────────┬────────────────────────────────────────┘
                         │ SQL / Supabase Client
┌────────────────────────▼────────────────────────────────────────┐
│                                                                  │
│                    MOTOR SCORING (Python)                       │
│                    (No cambios)                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ src/app/scoring.py:                                      │  │
│  │  - score_dataframe()                                     │  │
│  │  - score_from_tables()                                   │  │
│  │                                                          │  │
│  │ Capas (Pipeline Híbrido):                                │  │
│  │  1. NLP → add_narrative_similarity_features()           │  │
│  │  2. Reglas → calcular_score_reglas() [0-70]             │  │
│  │  3. ML → predict_fraud_proba() [0-20]                   │  │
│  │  4. Anomalías → predict_anomaly_scores() [0-10]         │  │
│  │  5. Score Final = 70%+20%+10% → [0-100]                 │  │
│  │                                                          │  │
│  │ Modelos cargados al startup:                             │  │
│  │  - fraud_lr.joblib (LogisticRegression)                 │  │
│  │  - fraud_iso.joblib (IsolationForest)                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└────────────────────────┬────────────────────────────────────────┘
                         │ SELECT / UPDATE
┌────────────────────────▼────────────────────────────────────────┐
│                                                                  │
│                  SUPABASE (PostgreSQL)                          │
│                                                                  │
│  Tablas:                                                        │
│   - siniestros (principal)         ← Aquí se guardan scores    │
│   - polizas (referencia)                                        │
│   - proveedores (referencia)                                    │
│   - documentos (referencia)                                     │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🔧 BACKEND - ESTRUCTURA Y FLUJO

### 1. Inicialización (`src/api/main.py`)

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Se ejecuta al startup de FastAPI"""
    # STARTUP: Cargar modelos en memoria (una sola vez)
    app.state.ml_model = load_model()          # fraud_lr.joblib
    app.state.anomaly_model = load_anomaly_model()  # fraud_iso.joblib
    app.state.ml_config = load_model_config()  # config JSON
    
    yield
    
    # SHUTDOWN: Limpiar recursos (opcional)
```

**Por qué?** Los modelos `.joblib` son pesados. Cargarlos una sola vez al startup es mucho más rápido que hacerlo en cada request.

### 2. Cliente Supabase (`src/api/deps.py`)

```python
class SupabaseClient:
    """Singleton que gestiona la conexión a Supabase"""
    
    def __init__(self):
        self.url = os.environ["SUPABASE_URL"]
        self.key = os.environ["SUPABASE_KEY"]
        self.client = create_client(self.url, self.key)
    
    @staticmethod
    def get():
        """Devuelve siempre la misma instancia"""
        if SupabaseClient._instance is None:
            SupabaseClient._instance = SupabaseClient()
        return SupabaseClient._instance.client
```

**Por qué?** Un único cliente compartido por toda la app, sin crear múltiples conexiones.

### 3. Repositorio (`src/api/services/__init__.py`)

Patrón **Repository** - separa lógica de acceso a datos:

```python
class SupabaseRepository:
    
    # LECTURA
    def fetch_siniestro(id):
        """SELECT * FROM siniestros WHERE id = ?"""
    
    def list_siniestros(semaforo, min_score, ...):
        """SELECT * FROM siniestros WHERE semaforo=? AND score>=?"""
    
    def fetch_scoring_tables():
        """Obtiene 4 DataFrames necesarios para scoring"""
        return {
            "siniestros": df_sin,
            "polizas": df_pol,
            "proveedores": df_prov,
            "documentos": df_doc,
        }
    
    # ESCRITURA
    def persist_score(id_siniestro, score_result):
        """UPDATE siniestros SET score_riesgo=?, semaforo_alerta=?, ..."""
    
    def batch_persist_scores(scores_df):
        """UPDATE múltiples siniestros en loop"""
```

### 4. Servicio de Scoring (`src/api/services/scoring_service.py`)

```python
class ScoringService:
    """Wrapper del motor Python"""
    
    def __init__(self, ml_model, anomaly_model, ml_config):
        self.ml_model = ml_model          # Cargado en startup
        self.anomaly_model = anomaly_model
        self.ml_config = ml_config
    
    def score_one_claim(tables, id_siniestro):
        """
        1. build_from_tables(tables) → construye features
        2. score_dataframe() → aplica scoring híbrido
        3. Devuelve Dict con resultado
        """
    
    def score_batch(tables):
        """Score a TODOS los siniestros"""
```

### 5. Routers (Endpoints)

#### Router: `siniestros.py`

```
GET /siniestros
├─ Parámetros: semaforo, min_score, cobertura, limit, offset
├─ Repo: list_siniestros()
└─ Retorna: { total: 1000, items: [...] }

GET /siniestros/{id}
├─ Repo: fetch_siniestro(id)
└─ Retorna: SiniestroDetalle (JSON)

POST /siniestros/{id}/score
├─ Repo: fetch_scoring_tables(id)
├─ Service: score_one_claim()
├─ Repo: persist_score()  ← Actualiza BD
└─ Retorna: ScoreResponse { score_final, semaforo, explicacion, ... }

POST /siniestros/score-all
├─ Repo: fetch_scoring_tables()  (todas las tablas)
├─ Service: score_batch()
├─ Repo: batch_persist_scores()  ← Actualiza todos
└─ Retorna: BatchScoreResponse { processed, semaforo_counts }
```

#### Router: `chat.py`

```
POST /siniestros/{id}/chat
├─ Request: { messages: [{ role, content }, ...] }
├─ Repo: fetch_siniestro(id)
├─ generate_chat_response()  ← STUB (falta OpenAI)
└─ Retorna: ChatResponse { reply, sources, timestamp }
```

#### Router: `health.py`

```
GET /health
├─ Verifica si modelos están cargados
└─ Retorna: HealthResponse { status, models_loaded, ml_threshold }
```

### 6. Schemas Pydantic (`schemas.py`)

Validación automática de datos:

```python
class SiniestroDetalle(BaseModel):
    id_siniestro: str
    codigo_siniestro: str
    score_riesgo: int = Field(ge=0, le=100)  ← Valida rango
    semaforo_alerta: str
    
    class Config:
        from_attributes = True  ← Convierte ORM objects

class ScoreResponse(BaseModel):
    score_final: int
    semaforo: str
    explicacion: str
    timestamp: datetime
```

---

## 🎨 FRONTEND - ESTRUCTURA Y COMPONENTES

### Tecnología

- **Vite** - Build tool (bundler moderno)
- **React 18** - Framework UI
- **Tailwind CSS** - Estilos (utility-first)
- **React Router** - Navegación
- **Axios** - HTTP client
- **Lucide Icons** - Iconos

### 1. Cliente API (`src/api/client.js`)

```javascript
const api = axios.create({
    baseURL: "http://localhost:8000",
});

export const siniestrosAPI = {
    health: () => api.get("/health"),
    list: (params) => api.get("/siniestros", { params }),
    get: (id) => api.get(`/siniestros/${id}`),
    score: (id) => api.post(`/siniestros/${id}/score`),
    scoreAll: () => api.post("/siniestros/score-all"),
    chat: (id, messages) => api.post(`/siniestros/${id}/chat`, { messages }),
};
```

**Por qué?** Centralizar las llamadas al backend en un lugar, facilita cambiar URLs, agregar headers de auth, etc.

### 2. Página: Listado de Siniestros (`src/pages/ListadoSiniestros.jsx`)

**Componentes:**
- Tabla con columnas: Código, Cobertura, Monto, Score, Semáforo
- Filtros: Semáforo, Score mínimo, Cobertura
- Botón "Recalcular todo" (POST /score-all)
- Botón "Ver detalle" por fila

**Estado (useState):**
```javascript
const [siniestros, setSiniestros] = useState([])     // Items tabla
const [total, setTotal] = useState(0)                // Total registros
const [loading, setLoading] = useState(true)
const [error, setError] = useState(null)
const [filters, setFilters] = useState({             // Filtros actuales
    semaforo: "",
    min_score: "",
    cobertura: "",
    limit: 50,
    offset: 0,
})
const [scoreAllLoading, setScoreAllLoading] = useState(false)
```

**Flujo:**
```
1. useEffect() → loadSiniestros() cuando cambian filtros
2. loadSiniestros() → siniestrosAPI.list(params)
3. setSiniestros(respuesta.items)
4. Render tabla con map()
5. Click en fila → navigate(`/siniestro/${id}`)
```

### 3. Página: Detalle de Siniestro (`src/pages/DetalleSiniestro.jsx`)

**Layout:**
```
┌─────────────────────────────┬──────────────┐
│                             │              │
│ Info General                │ Asistente    │
│ ─────────────────           │ Chat         │
│ - Cobertura, sucursal,      │ ─────────────│
│   montos                    │ Messages +   │
│                             │ Input        │
│ Análisis de Riesgo          │              │
│ ─────────────────           │              │
│ - Score bar                 │              │
│ - Desglose: Reglas/ML/Anom  │              │
│ - Explicación               │              │
│ - Botón Recalcular          │              │
│                             │              │
│ Descripción Narrativa       │              │
│ ─────────────────           │              │
│ (si existe)                 │              │
└─────────────────────────────┴──────────────┘
```

**Flujo de Scoring:**
```
1. User click en "Recalcular"
2. siniestrosAPI.score(id)  ← POST /siniestros/{id}/score
3. Backend:
   a. fetch_scoring_tables(id)
   b. score_one_claim()
   c. persist_score()  ← Guarda en Supabase
   d. Retorna ScoreResponse
4. Frontend:
   a. Actualiza estado local: setSiniestro(newData)
   b. Re-render con nuevos valores
```

**Flujo de Chat:**
```
1. User escribe mensaje y presiona Enter
2. newMessages = [...chatMessages, { role: "user", content }]
3. setChatMessages(newMessages)
4. siniestrosAPI.chat(id, newMessages)
5. Backend:
   a. fetch_siniestro(id)
   b. generate_chat_response()  ← STUB
   c. Retorna ChatResponse
6. Frontend:
   a. setChatMessages([...prev, { role: "assistant", content }])
   b. Re-render conversation
```

### 4. Componentes Reutilizables

#### `SemaforoIndicador.jsx`
```javascript
// Entrada: semaforo = "VERDE" | "AMARILLO" | "ROJO"
// Salida: <span className="badge badge-success">VERDE</span>

const config = {
    VERDE: { badge: "badge-success" },
    AMARILLO: { badge: "badge-warning" },
    ROJO: { badge: "badge-danger" },
}
```

#### `ScoreBar.jsx`
```javascript
// Entrada: score = 42
// Salida: Barra visual (0-100) con número

const percentage = (score / 100) * 100
const bgColor = score > 75 ? "bg-red-500" : 
                score > 40 ? "bg-yellow-500" : 
                "bg-green-500"

// <div className={bgColor} style={{width: "42%"}} />
// 42/100
```

### 5. Estilos (`src/index.css`)

```css
@tailwind base;        /* Reset de Tailwind */
@tailwind components;  /* Clases Tailwind */
@tailwind utilities;   /* Utilidades Tailwind */

/* Clases personalizadas */
.semaforo-verde { @apply bg-green-50 border-l-4 border-green-500; }
.semaforo-amarillo { @apply bg-yellow-50 border-l-4 border-yellow-500; }
.semaforo-rojo { @apply bg-red-50 border-l-4 border-red-500; }
```

---

## 🔄 FLUJO DE DATOS END-TO-END

### Caso 1: Ver Listado de Siniestros

```
User abre http://localhost:3000
│
├─ App.jsx → Router
│  └─ Route "/" → ListadoSiniestros
│
├─ ListadoSiniestros mount
│  └─ useEffect() →
│     └─ loadSiniestros()
│        └─ siniestrosAPI.list({ limit: 50, offset: 0 })
│           │
│           └─ HTTP GET http://localhost:8000/siniestros?limit=50&offset=0
│              │
│              └─ Backend:
│                 ├─ routers/siniestros.py → list_siniestros()
│                 ├─ services/__init__.py → repo.list_siniestros()
│                 ├─ Supabase:
│                 │  └─ SELECT * FROM siniestros LIMIT 50 OFFSET 0
│                 └─ Retorna: { total: 1000, items: [...] }
│
├─ setSiniestros(response.data.items)
│
└─ Render tabla con map(siniestros)
   └─ Cada fila: <Link to={`/siniestro/${id}`}>Ver detalle →</Link>
```

### Caso 2: Calcular Score

```
User en detalle, click "Recalcular"
│
├─ DetalleSiniestro.jsx → handleScore()
│
├─ siniestrosAPI.score(id)
│  │
│  └─ HTTP POST http://localhost:8000/siniestros/{id}/score
│     │
│     └─ Backend: routers/siniestros.py → score_siniestro()
│        │
│        ├─ repo.fetch_scoring_tables(id)  ← 4 DataFrames de Supabase
│        │
│        ├─ scoring_service.score_one_claim()
│        │  ├─ build_from_tables() → features
│        │  ├─ apply_nlp_layer() → narrative_similarity
│        │  ├─ apply_rules() → score_reglas [0-70]
│        │  ├─ predict_fraud_proba() → ml_proba [0-20]
│        │  ├─ predict_anomaly_scores() → anom_score [0-10]
│        │  └─ compute_hybrid_score() → score_final [0-100]
│        │
│        ├─ repo.persist_score(id, result)
│        │  └─ UPDATE siniestros SET score_riesgo=42, semaforo_alerta='AMARILLO', ...
│        │
│        └─ Retorna: ScoreResponse { score_final, semaforo, explicacion, ... }
│
├─ setSiniestro(newData) → actualiza estado
│
└─ Re-render con nuevos valores
   ├─ ScoreBar muestra nueva barra
   ├─ SemaforoIndicador cambia color
   └─ Explicación se actualiza
```

### Caso 3: Chat Conversacional

```
User escribe "¿Por qué está en amarillo?" y presiona Enter
│
├─ DetalleSiniestro.jsx → handleChatSend()
│
├─ newMessages = [...chatMessages, { role: "user", content: "¿Por qué..." }]
│
├─ setChatMessages(newMessages) → render inmediato
│
├─ siniestrosAPI.chat(id, newMessages)
│  │
│  └─ HTTP POST http://localhost:8000/siniestros/{id}/chat
│     │
│     │  Payload: {
│     │    "messages": [
│     │      { "role": "user", "content": "¿Por qué está en amarillo?" }
│     │    ]
│     │  }
│     │
│     └─ Backend: routers/chat.py → chat()
│        │
│        ├─ repo.fetch_siniestro(id) → obtener datos
│        │
│        ├─ generate_chat_response(id, messages, siniestro_data)
│        │  └─ (STUB) Devuelve respuesta hardcodeada
│        │     TODO: Integrar OpenAI
│        │
│        └─ Retorna: ChatResponse {
│           "reply": "El siniestro tiene score 42 porque...",
│           "sources": ["score_riesgo", "explicacion_riesgo"],
│           "timestamp": "2026-05-29T..."
│        }
│
├─ setChatMessages([...prev, { role: "assistant", content: reply }])
│
└─ Re-render conversación
   └─ Nuevo mensaje del asistente aparece
```

---

## 💾 BASE DE DATOS (SUPABASE)

### Tablas Utilizadas

```sql
-- Tabla principal (se actualiza)
CREATE TABLE siniestros (
    id_siniestro UUID PRIMARY KEY,
    codigo_siniestro VARCHAR(20),
    cobertura VARCHAR(20),
    sucursal VARCHAR(20),
    monto_reclamado DECIMAL(15,2),
    monto_estimado DECIMAL(15,2),
    descripcion_narrativa TEXT,
    estado_tramite VARCHAR(20),
    
    -- ✅ Columnas que el backend ACTUALIZA:
    score_riesgo INT DEFAULT 0,              -- [0-100]
    semaforo_alerta VARCHAR(20) DEFAULT 'VERDE',  -- VERDE/AMARILLO/ROJO
    explicacion_riesgo TEXT,                 -- Texto con explicación
    ml_proba NUMERIC(6,4),                  -- [0-1]
    score_reglas INT,                        -- [0-70]
    ml_alerta SMALLINT DEFAULT 0,            -- 0 o 1
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Tablas de referencia (sin cambios)
CREATE TABLE polizas (
    id_poliza UUID PRIMARY KEY,
    id_siniestro UUID REFERENCES siniestros,
    monto_asegurado DECIMAL(15,2),
    vigencia_inicio DATE,
    vigencia_fin DATE
);

CREATE TABLE proveedores (
    id_proveedor UUID PRIMARY KEY,
    id_siniestro UUID REFERENCES siniestros,
    lista_restrictiva BOOLEAN,
    tipo_proveedor VARCHAR(50)
);

CREATE TABLE documentos (
    id_documento UUID PRIMARY KEY,
    id_siniestro UUID REFERENCES siniestros,
    adulteracion_flag BOOLEAN,
    inconsistencia_flag BOOLEAN
);
```

### Flujo de Datos en Supabase

```
1. Inicialización (una sola vez):
   └─ python -m src.ingestion.load_data
      └─ Genera ~1000 siniestros sintéticos en BD

2. Training (una sola vez):
   └─ python scripts/train_fraud_model.py
      └─ Genera fraud_lr.joblib y fraud_iso.joblib

3. En operación (para cada scoring):
   
   Backend:
   ├─ SELECT siniestros WHERE id = ?  ← Lee datos actuales
   ├─ SELECT polizas WHERE id_siniestro = ?
   ├─ SELECT proveedores WHERE id_siniestro = ?
   ├─ SELECT documentos WHERE id_siniestro = ?
   │
   ├─ [Procesa en Python] ← sin acceder BD
   │
   └─ UPDATE siniestros SET
      score_riesgo = ?,
      semaforo_alerta = ?,
      explicacion_riesgo = ?,
      ... ← Guarda resultado
```

---

## 📂 DETALLES DE CADA ARCHIVO

### Backend

#### `src/api/main.py` (100 líneas)
```
├─ Imports necesarios
├─ lifespan() context manager
│  ├─ Startup: Carga ml_model, anomaly_model, ml_config
│  └─ Shutdown: (vacío, pero puede limpiar recursos)
├─ FastAPI app con middleware CORS
├─ Routers incluidos:
│  ├─ health router
│  ├─ siniestros router
│  └─ chat router
└─ Root endpoint "/"
```

**Responsabilidad:** Orquestar la app, cargar modelos una vez.

#### `src/api/schemas.py` (120 líneas)
```
├─ SiniestroBase (campos comunes)
├─ SiniestroCreate (para POST)
├─ SiniestroDetalle (con scores)
├─ SiniestroListResponse (para GET /)
├─ ScoreRequest / ScoreResponse
├─ ChatMessage / ChatRequest / ChatResponse
├─ HealthResponse
└─ BatchScoreResponse
```

**Responsabilidad:** Definir contratos API (validación automática).

#### `src/api/deps.py` (40 líneas)
```
├─ SupabaseClient class
│  ├─ __init__(): Conecta con SUPABASE_URL y SUPABASE_KEY
│  ├─ get(): Devuelve singleton
│  └─ reset(): Para testing
└─ get_supabase_client() dependency
```

**Responsabilidad:** Gestionar conexión a Supabase (singleton).

#### `src/api/services/__init__.py` (130 líneas)
```
├─ SupabaseRepository class
│  ├─ fetch_siniestro(id)
│  ├─ list_siniestros(filters)
│  ├─ fetch_scoring_tables(id?)
│  ├─ persist_score(id, result)
│  └─ batch_persist_scores(df)
```

**Responsabilidad:** Encapsular acceso a datos (patrón Repository).

#### `src/api/services/scoring_service.py` (60 líneas)
```
├─ ScoringService class
│  ├─ __init__(ml_model, anomaly_model, ml_config)
│  ├─ score_one_claim(tables, id)
│  ├─ score_batch(tables)
│  └─ get_semaforo_counts(tables)
```

**Responsabilidad:** Wrapper del motor Python (importa score_dataframe).

#### `src/api/routers/siniestros.py` (150 líneas)
```
├─ GET /
│  └─ list_siniestros() con filtros
├─ GET /{id}
│  └─ get_siniestro(id)
├─ POST /{id}/score
│  └─ score_siniestro(id) → fetch → score → persist → return
└─ POST /score-all
   └─ score_all_siniestros() → batch
```

**Responsabilidad:** Endpoints REST para siniestros.

#### `src/api/routers/chat.py` (80 líneas)
```
├─ generate_chat_response() [STUB]
│  └─ TODO: Integrar OpenAI
└─ POST /{id}/chat
   └─ chat(id, messages)
```

**Responsabilidad:** Endpoint chat (a mejorar).

#### `src/api/routers/__init__.py` (20 líneas)
```
└─ GET /health
   └─ Health check + status modelos
```

**Responsabilidad:** Verificar que API está viva y modelos cargados.

### Frontend

#### `src/App.jsx` (60 líneas)
```
├─ useEffect() → checkAPI()
│  └─ Verifica GET /health
├─ BrowserRouter con Routes
│  ├─ "/" → ListadoSiniestros
│  └─ "/siniestro/:id" → DetalleSiniestro
└─ Alert si API no está disponible
```

**Responsabilidad:** App principal, routing, health check.

#### `src/pages/ListadoSiniestros.jsx` (200 líneas)
```
├─ useState() para siniestros, filtros, loading
├─ useEffect() → loadSiniestros() cuando cambian filtros
├─ handleFilterChange()
├─ handleScoreAll() → POST /score-all
└─ Render
   ├─ Filtros (select + input)
   ├─ Tabla con columnas
   └─ Cada fila con Link a detalle
```

**Responsabilidad:** Listar siniestros con filtros y opciones de scoring batch.

#### `src/pages/DetalleSiniestro.jsx` (300 líneas)
```
├─ useParams(), useNavigate()
├─ useState() para siniestro, chat, loading
├─ useEffect() → loadSiniestro(id)
├─ handleScore() → POST /score
├─ handleChatSend() → POST /chat
└─ Render
   ├─ Back button
   ├─ Info general
   ├─ Análisis riesgo
   ├─ Descripción narrativa
   └─ Chat panel (derecha)
```

**Responsabilidad:** Detalle del siniestro, scoring y chat.

#### `src/components/SemaforoIndicador.jsx` (30 líneas)
```
├─ Props: semaforo (VERDE/AMARILLO/ROJO)
└─ Render: <span className="badge badge-{tipo}">
```

**Responsabilidad:** Mostrar badge con color según semáforo.

#### `src/components/ScoreBar.jsx` (35 líneas)
```
├─ Props: score (0-100)
├─ Calcula: percentage, bgColor
└─ Render: <div style={{width: percentage%}} />
```

**Responsabilidad:** Barra visual del score.

#### `src/components/Navbar.jsx` (20 líneas)
```
├─ Link a home
└─ Título + descripción
```

**Responsabilidad:** Barra de navegación.

#### `src/api/client.js` (40 líneas)
```
├─ axios.create() con baseURL
├─ Interceptor para errores
└─ siniestrosAPI object con métodos:
   ├─ health()
   ├─ list(params)
   ├─ get(id)
   ├─ score(id)
   ├─ scoreAll()
   └─ chat(id, messages)
```

**Responsabilidad:** Cliente HTTP centralizado.

#### `src/index.css` (100 líneas)
```
├─ @tailwind directives
├─ Clases personalizadas (.badge, .btn, .card, etc.)
└─ Semáforo styles (.semaforo-verde, .semaforo-amarillo, .semaforo-rojo)
```

**Responsabilidad:** Estilos globales con Tailwind.

### Configuración

#### `package.json` (50 líneas)
```
├─ name: aura-frontend
├─ scripts:
│  ├─ dev: vite
│  ├─ build: vite build
│  └─ preview: vite preview
├─ dependencies:
│  ├─ react
│  ├─ react-dom
│  ├─ react-router-dom
│  ├─ axios
│  └─ lucide-react
└─ devDependencies:
   ├─ @vitejs/plugin-react
   ├─ vite
   ├─ tailwindcss
   └─ ...
```

#### `vite.config.js` (15 líneas)
```
├─ React plugin
├─ Dev server puerto 3000
└─ Proxy /api → http://localhost:8000
```

#### `tailwind.config.js` (20 líneas)
```
├─ content: src/**/*.{js,jsx}
└─ theme:
   └─ extend: colors, fonts
```

---

## 🔨 CÓMO EXTENDER

### 1. Agregar nuevo endpoint Backend

**Paso 1:** Crear router en `src/api/routers/new_feature.py`

```python
from fastapi import APIRouter
from src.api.schemas import YourSchema
from src.api.deps import get_repo

router = APIRouter()

@router.get("/your-endpoint")
async def your_endpoint(param: str, repo = Depends(get_repo)):
    # Lógica aquí
    return { "result": "..." }
```

**Paso 2:** Incluir en `src/api/main.py`

```python
from src.api.routers import new_feature

app.include_router(
    new_feature.router,
    prefix="/your-prefix",
    tags=["your-tag"]
)
```

**Paso 3:** Agregar schema en `schemas.py`

```python
class YourSchema(BaseModel):
    field1: str
    field2: int
```

### 2. Agregar componente React

**Paso 1:** Crear en `src/components/NewComponent.jsx`

```javascript
function NewComponent({ prop1, prop2 }) {
    return (
        <div className="card">
            <h2>{prop1}</h2>
            {/* JSX aquí */}
        </div>
    );
}

export default NewComponent;
```

**Paso 2:** Importar en página

```javascript
import NewComponent from '../components/NewComponent';

function MyPage() {
    return (
        <div>
            <NewComponent prop1="test" prop2={42} />
        </div>
    );
}
```

### 3. Agregar nueva página React

**Paso 1:** Crear en `src/pages/NewPage.jsx`

```javascript
function NewPage() {
    return <div>Nueva página</div>;
}

export default NewPage;
```

**Paso 2:** Agregar ruta en `App.jsx`

```javascript
<Route path="/new-page" element={<NewPage />} />
```

### 4. Integrar OpenAI para Chat

**Paso 1:** Instalar cliente

```bash
pip install openai
```

**Paso 2:** Editar `src/api/routers/chat.py`

```python
import openai

def generate_chat_response(id_siniestro, messages, siniestro_data):
    openai.api_key = os.environ["OPENAI_API_KEY"]
    
    system_prompt = f"""Eres experto en detección de fraude.
    Score: {siniestro_data['score_riesgo']}
    Semáforo: {siniestro_data['semaforo_alerta']}
    Explicación: {siniestro_data['explicacion_riesgo']}"""
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            *messages,
        ],
        temperature=0.7,
    )
    
    return response.choices[0].message.content
```

**Paso 3:** Agregar `OPENAI_API_KEY` en `.env`

```env
OPENAI_API_KEY=sk-...
```

---

## 📖 REFERENCIAS

- [GUIA_BACK_FRONT.md](./GUIA_BACK_FRONT.md) - Guía original técnica
- [SETUP_COMPLETO.md](./SETUP_COMPLETO.md) - Cómo arrancar
- [TODO.md](./TODO.md) - Tareas pendientes
- [docs/uso_ia.md](./docs/uso_ia.md) - Motor de scoring
- FastAPI Docs: http://localhost:8000/docs
- React Docs: https://react.dev
- Tailwind CSS: https://tailwindcss.com

---

**Fin del documento**

Última actualización: Mayo 29, 2026  
Versión: 1.0 MVP
