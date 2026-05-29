# TODO - Tareas pendientes para A.U.R.A (Back + Front)

## ✅ COMPLETADO

### Backend (FastAPI)
- [x] Estructura base (main.py, routers, servicios)
- [x] Schemas Pydantic (request/response)
- [x] Integración Supabase
- [x] Endpoints REST:
  - [x] `GET /health` - Health check
  - [x] `GET /siniestros` - Listar con filtros
  - [x] `GET /siniestros/{id}` - Detalle
  - [x] `POST /siniestros/{id}/score` - Scoring individual
  - [x] `POST /siniestros/score-all` - Batch scoring
  - [x] `POST /siniestros/{id}/chat` - Chat (stub)

### Frontend (React)
- [x] Setup con Vite + Tailwind CSS
- [x] Estructura de componentes
- [x] Páginas:
  - [x] Listado de siniestros (tabla, filtros, paginación)
  - [x] Detalle de siniestro (análisis, chat)
- [x] Cliente HTTP (axios)
- [x] Componentes reutilizables:
  - [x] SemaforoIndicador
  - [x] ScoreBar
  - [x] Navbar

---

## ⚠️ EN PROGRESO - Agente LLM Chat

**Archivo:** `src/api/routers/chat.py`

**Función:** `generate_chat_response()` - Actualmente devuelve respuestas básicas

### ¿Qué hacer?

Implementar con una de estas opciones:

#### Opción A: OpenAI API (Recomendado)
```python
import openai

def generate_chat_response(id_siniestro: str, messages: list, siniestro_data: dict) -> str:
    """Usar GPT-4 o GPT-3.5 para explicar el siniestro"""
    
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    
    system_prompt = f"""Eres un asistente experto en detección de fraude en siniestros.
    
    Datos del siniestro:
    - Score de riesgo: {siniestro_data.get('score_riesgo', 0)}/100
    - Semáforo: {siniestro_data.get('semaforo_alerta', 'VERDE')}
    - Explicación: {siniestro_data.get('explicacion_riesgo', '')}
    - ML Probabilidad: {siniestro_data.get('ml_proba', 0):.2%}
    
    Responde en español, de forma clara y concisa."""
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            *messages,  # Historial del chat
        ],
        temperature=0.7,
    )
    
    return response.choices[0].message.content
```

#### Opción B: Anthropic Claude
```python
import anthropic

def generate_chat_response(id_siniestro: str, messages: list, siniestro_data: dict) -> str:
    """Usar Claude para explicar el siniestro"""
    
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    
    formatted_messages = [
        {"role": m["role"], "content": m["content"]}
        for m in messages
    ]
    
    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1024,
        system=f"""Eres un asistente experto en detección de fraude en siniestros.
        
Score: {siniestro_data.get('score_riesgo', 0)}/100
Semáforo: {siniestro_data.get('semaforo_alerta', 'VERDE')}
Explicación: {siniestro_data.get('explicacion_riesgo', '')}""",
        messages=formatted_messages,
    )
    
    return response.content[0].text
```

#### Opción C: Ollama Local (Sin API key)
```python
import requests

def generate_chat_response(id_siniestro: str, messages: list, siniestro_data: dict) -> str:
    """Usar modelo local con Ollama"""
    
    prompt = f"""Explicar por qué este siniestro tiene score {siniestro_data.get('score_riesgo')}/100.
    
Contexto: {siniestro_data.get('explicacion_riesgo')}

Pregunta: {messages[-1].get('content')}"""
    
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "mistral", "prompt": prompt, "stream": False}
    )
    
    return response.json()["response"]
```

---

## 📋 PENDIENTE

### 1. Mejorar Chat (Backend)
- [ ] Integrar OpenAI / Claude / Ollama
- [ ] Almacenar historial de chats en Supabase
- [ ] Mejorar prompts del sistema para contexto del siniestro
- [ ] Agregar sources/referencias en respuesta

### 2. Frontend Enhancements
- [ ] Dashboard con gráficos (Chart.js)
- [ ] Exportar reportes a PDF
- [ ] Búsqueda por código siniestro
- [ ] Historial de cambios en score
- [ ] Tema oscuro
- [ ] Validación de formarios mejorada

### 3. Backend Enhancements
- [ ] Autenticación (JWT / OAuth)
- [ ] Roles y permisos (admin, analista, viewer)
- [ ] Audit log (quién vio qué, quién cambió scores)
- [ ] Rate limiting
- [ ] Caché de resultados
- [ ] Webhooks para cambios de score

### 4. Database
- [ ] Agregar columna `audit_log` en siniestros
- [ ] Agregar tabla `chat_history`
- [ ] Índices para queries comunes
- [ ] Backups automáticos

### 5. Deploy
- [ ] Docker (Backend + Frontend)
- [ ] CI/CD (GitHub Actions)
- [ ] Environment-specific configs
- [ ] Health checks mejorados

---

## 🧪 Testing

### Backend
```bash
# Instalar pytest
pip install pytest pytest-asyncio httpx

# Crear tests/test_api.py
pytest tests/
```

### Frontend
```bash
# Instalar vitest + testing-library
npm install -D vitest @testing-library/react @testing-library/jest-dom

# npm run test
```

### E2E (Cypress)
```bash
npm install -D cypress
npx cypress open
```

---

## 🎯 Prioridad INMEDIATA

1. **Integrar OpenAI Chat** (sin esto, el chat es stub)
2. **Pruebas en Supabase** (asegurar que datos se guardan)
3. **Testing del scoring** (verificar que scores son correctos)
4. **Deploy local** (Docker o manual)

---

## 🔗 Referencias

- Endpoint chat: `src/api/routers/chat.py` (línea ~20)
- Config OpenAI: Variables en `.env`
- Docs FastAPI: http://localhost:8000/docs (una vez corriendo)

---

## 📞 Contacto / Soporte

Si hay errores:
1. Ver logs en terminal del backend
2. Verificar `.env` (SUPABASE_URL, SUPABASE_KEY)
3. Confirmar que modelos existen: `python scripts/run_scoring.py`
4. Revisar CORS en `src/api/main.py` si hay errores en frontend
