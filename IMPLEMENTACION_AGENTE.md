# 📋 Implementación del Agente OpenAI - A.U.R.A

**Propósito:** Documentación viva de cambios, lógica y arquitectura mientras implementamos el chat con OpenAI.

**Última actualización:** 2026-05-29

---

## 📊 Índice de Cambios

| Fase | Componente | Estado | Fecha |
|------|-----------|--------|-------|
| 1 | OpenAI API setup | ✅ Completado | 2026-05-29 |
| 2 | Claims Agent | ✅ Completado | 2026-05-29 |
| 3 | Chat Router | ✅ Completado | 2026-05-29 |
| 4 | Testing E2E | ⏳ En progreso | - |

---

## 🎯 Objetivo General

Integrar un agente conversacional con **OpenAI** que:
- Explique decisiones de scoring al analista
- Responda preguntas sobre el caso
- Use contexto del siniestro (score, reglas, narrativa, ML proba)
- No reemplace el scoring, solo lo justifique

---

## 🏗️ Arquitectura del Agente

```
Cliente React
    ↓ POST /siniestros/{id}/chat
FastAPI (Chat Router)
    ↓ get_repo() + get_siniestro()
SupabaseRepository
    ↓ fetch_scoring_tables()
Contexto: {score, explicación, narrativa, ml_proba}
    ↓
Claims Agent (claims_agent.py)
    ↓ run_claims_agent(messages, context)
OpenAI API (GPT-3.5-turbo)
    ↓
Response JSON
    ← Cliente React (muestra en chat panel)
```

---

## 📝 Cambios Realizados

### [FASE 1] OpenAI Setup

#### 1.1 Verificar dependencias
**Archivo:** `requirements.txt`
**Estado:** ✅ Ya incluye `openai` y `langchain`
**Qué hace:** Librería OpenAI para llamadas a API
```
openai>=1.0.0
langchain>=0.1.0
```

#### 1.2 Configurar variables de entorno
**Archivo:** `.env`
**Acción:** Agregar `OPENAI_API_KEY=sk-...`
**Obtener de:** https://platform.openai.com/api-keys
```env
OPENAI_API_KEY=sk-proj-... (generado en OpenAI)
```

---

### [FASE 2] Implementar Claims Agent ✅

#### 2.1 Crear agent principal ✅
**Archivo:** `src/agents/claims_agent.py`
**Responsabilidad:** 
- Construir prompt del sistema con contexto del caso
- Llamar OpenAI GPT-3.5-turbo con historial de mensajes
- Procesar respuesta y devolverla

**Componentes implementados:**

```python
class ClaimsAgent:
  __init__()                    # Inicializa cliente OpenAI (carga API key de .env)
  build_system_prompt()         # Genera prompt con contexto del siniestro
  run()                         # Ejecuta OpenAI API con modelo GPT-3.5-turbo
  _generate_fallback_response() # Genera respuesta simulada si OpenAI no disponible

Funciones públicas:
  run_claims_agent()            # Wrapper para usar el agente
  get_agent()                   # Singleton para evitar crear múltiples clientes
```

**System Prompt incluye:**
- Código y score del siniestro
- Explicación automática del scoring
- Narrativa completa del evento  
- Probabilidad ML y score de reglas
- Instrucciones claras (NO reemplazar scoring, usar "señales de riesgo")

**Fallback Automático (2026-05-29):**
- Detecta errores 429 (quota excedida) en OpenAI
- Genera respuesta simulada realista basada en contexto
- Permite testing de UI sin bloqueos por billing
- Logs: `⚠️  [AGENT] OpenAI quota excedida - usando respuesta fallback`
- Una vez actives crédito en OpenAI, sistema usa API real automáticamente

---

### [FASE 3] Actualizar Chat Router ✅

#### 3.1 Integrar OpenAI en endpoint `/chat` ✅
**Archivo:** `src/api/routers/chat.py`
**Estado:** Mejorado con error handling robusto

**Cambios realizados (v2 - error handling):**

1. **Imports:**
   ```python
   from src.agents.claims_agent import run_claims_agent
   ```

2. **Function build_context_for_agent():**
   - Mapea campos de BD a contexto OpenAI
   - Usa valores default si campos faltantes
   - Robusto ante datos incompletos

3. **Endpoint `/chat` mejorado:**
   ```python
   # Validación robusta:
   - Verifica siniestro existe
   - Convierte mensajes a dict si es Pydantic
   - Filtra mensajes válidos
   - Error handling completo con tracebacks
   
   # Try/catch para:
   - HTTPException (404 siniestro no encontrado)
   - ValueError (OPENAI_API_KEY faltante)
   - Exception (cualquier otro error)
   ```

4. **Manejo de datos:**
   - Acepta tanto dict como Pydantic ChatMessage
   - Valida que contexto sea dict
   - Valida que haya mensajes
   - Filtra mensajes vacíos

#### 3.2 Mejorado Claims Agent ✅
**Archivo:** `src/agents/claims_agent.py`
**Estado:** Error handling mejorado

**Cambios en `run()` method:**
```python
# Nuevas validaciones:
- Verificar contexto no None y es dict
- Verificar messages no vacío
- Filtrar mensajes válidos
- Traceback en logs para debugging

# Manejo de excepciones:
- ValueError → error de configuración
- Exception → error general con traceback
```

**Endpoint:**
```
POST /siniestros/{id}/chat
Body: { "messages": [{"role": "user", "content": "¿Por qué alto riesgo?"}] }
Response: { "reply": "Indicadores de riesgo: ...", "status": "ok" }
```

---

## 🔑 Contexto del Siniestro (Qué envía el agente a OpenAI)

```python
context = {
    "codigo_siniestro": "SIN-2026-0001",
    "score_riesgo": 68,
    "semaforo_alerta": "AMARILLO",
    "explicacion": "Cálculo: 35 reglas + 20 ML + 13 anomalía = 68",
    "cobertura": "ROBO",
    "monto_reclamado": 2762.36,
    "descripcion_narrativa": "EL ASEGURADO REPORTA ROBO EN LOJA...",
    "ml_proba": 0.65,
    "score_reglas": 35,
    "anom_score": 13,
}
```

**System Prompt base:**
```
Eres A.U.R.A, asistente de analistas de siniestros.
Respondes en español, breve y profesional.

CONTEXTO DEL CASO:
- Código: {codigo_siniestro}
- Score: {score_riesgo}/100 ({semaforo_alerta})
- Explicación: {explicacion}
- Cobertura: {cobertura}
- Narrativa: {descripcion_narrativa}
- ML Probabilidad: {ml_proba}

Tu rol:
✓ Explicar indicadores de riesgo
✓ Responder preguntas sobre el caso
✗ NO reemplazar decisiones del scoring
✗ NO afirmar fraude confirmado - usar "señales de riesgo"
```

---

## 🔧 Dependencias y Imports

**Nuevos imports necesarios:**
```python
# src/agents/claims_agent.py
from openai import OpenAI
from typing import List, Dict
import os
from dotenv import load_dotenv

# src/api/routers/chat.py
from src.agents.claims_agent import run_claims_agent
```

---

## 📞 Flujo de Integración

### Request del Cliente

```javascript
// frontend: POST /siniestros/{id}/chat
POST http://localhost:8000/siniestros/sin-e06928a9/chat
{
  "messages": [
    { "role": "user", "content": "¿Por qué tan alto el riesgo?" }
  ]
}
```

### Procesamiento Backend

```
1. Chat Router recibe request
2. Extrae id_siniestro y messages
3. Llama repo.fetch_scoring_tables(id)
4. Construye context dict
5. Llama run_claims_agent(messages, context)
6. OpenAI retorna respuesta
7. Devuelve JSON al cliente
```

### Response al Cliente

```json
{
  "reply": "El score de 68 indica AMARILLO por...",
  "status": "ok",
  "tokens_used": 145
}
```

---

## ⚠️ Casos de Error

| Error | Causa | Solución |
|-------|-------|----------|
| `OpenAI API key not found` | OPENAI_API_KEY no en .env | Agregar clave en .env |
| `Siniestro no encontrado` | ID inválido | Validar ID en frontend |
| `RateLimitError` | Cuota excedida | Esperar o agregar más fondos a OpenAI |
| `Context window exceeded` | Mensajes muy largos | Limitar historial |

---

## 🧪 Testing Manual

**Paso 1:** Obtener ID válido
```bash
curl http://localhost:8000/siniestros?limit=1
# Copiar id_siniestro del primer resultado
```

**Paso 2:** Llamar endpoint chat
```bash
curl -X POST http://localhost:8000/siniestros/{id_siniestro}/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "¿Por qué este score?"}
    ]
  }'
```

**Paso 3:** Verificar respuesta
```json
{
  "reply": "El análisis indica...",
  "status": "ok"
}
```

---

## 📁 Archivos Modificados / Creados

| Archivo | Cambio | Estado | Razón |
|---------|--------|--------|-------|
| `src/agents/claims_agent.py` | Implementar clase ClaimsAgent + run_claims_agent() | ✅ Done | Lógica del agente OpenAI |
| `src/api/routers/chat.py` | Reemplazar stub + integrar agente | ✅ Done | Endpoint chat funcional |
| `.env` | Agregar OPENAI_API_KEY | ⚠️ Manual | Autenticación con OpenAI |
| `IMPLEMENTACION_AGENTE.md` | Crear documento vivo | ✅ Done | Documentación de cambios |
| `requirements.txt` | ✓ Ya tiene openai | ✅ Done | Dependencias OK |

---

## 🚀 Próximos Pasos

- [x] Implementar `claims_agent.py`
- [x] Actualizar `chat.py` router
- [ ] **Agregar OPENAI_API_KEY en `.env`** ← CRITICAL (sin esto no funciona)
- [ ] Test manual desde Swagger `/docs`
- [ ] Test E2E desde frontend (chat panel)
- [ ] Ajustar temperatura y max_tokens si es necesario

### ⚡ Paso Crítico: Agregar API Key OpenAI

1. Ir a: https://platform.openai.com/api-keys
2. Crear nueva API key (o copiar una existente)
3. En `.env`, reemplazar:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```
   Por:
   ```
   OPENAI_API_KEY=sk-proj-... (tu clave real)
   ```
4. Guardar `.env`
5. El servidor se recargará automáticamente (--reload)

Sin este paso, al intentar usar chat verás:
```
ValueError: OPENAI_API_KEY no está configurada en .env
```

---

## 📌 Notas Importantes

1. **No reinventar:** Solo usar OpenAI, no modificar scoring
2. **Contexto es rey:** El prompt debe incluir todo lo necesario
3. **Error handling:** Capturar errores de API y devolverlos amigables
4. **Rate limit:** OpenAI tiene cuotas - monitorear uso
5. **Costo:** Cada llamada cuesta dinero - optimizar prompts

---

## 🔄 Ciclo de Vida del Chat

**Usuario:** "¿Por qué AMARILLO?"
    ↓
**Frontend:** POST /siniestros/{id}/chat
    { "messages": [{"role": "user", "content": "¿Por qué AMARILLO?"}] }
    ↓
**Chat Router:** 
    1. Obtiene siniestro de Supabase
    2. Construye contexto con score/narrativa/etc
    3. Llama run_claims_agent()
    ↓
**Claims Agent:**
    1. Carga OPENAI_API_KEY de .env
    2. Construye system prompt con contexto
    3. Llama OpenAI GPT-3.5-turbo
    4. Devuelve respuesta
    ↓
**Frontend:** Muestra en chat panel
    "El score de 68 (AMARILLO) indica señales de riesgo..."

---

## 🧠 Decisiones de Diseño

### Modelo: GPT-3.5-turbo (actualizado 2026-05-29)
**Cambio realizado:** Inicial planeado GPT-4 → Actual GPT-3.5-turbo

**Razón del cambio:**
- GPT-4 requiere acceso específico en OpenAI (error 404: "model does not exist or you do not have access")
- GPT-3.5-turbo está disponible para todos los usuarios con API key válida
- Rendimiento suficiente para análisis de siniestros
- Más rápido (latencia ~0.5s vs 1-2s de GPT-4)
- Menor costo

**Alternativa en el futuro:**
- Si tenés acceso a GPT-4 en tu cuenta OpenAI: cambiar `self.model = "gpt-4"` en `src/agents/claims_agent.py` línea 28

### ¿Por qué no guardar mensajes en BD?
- Prototipo MVP
- Historial es volátil (se pierde al cerrar sesión)
- Producción: agregar tabla `chats` en Supabase

### ¿Por qué build_context_for_agent()?
- Separación de responsabilidades
- Fácil de testear contexto sin OpenAI
- Reutilizable si hay múltiples agentes

---

## 🐛 Troubleshooting

### "NotFoundError: The model 'gpt-4' does not exist or you do not have access" (404)
**Problema:** Tu API key no tiene acceso a GPT-4
**Solución:** Cambiar a `gpt-3.5-turbo` en `src/agents/claims_agent.py` línea 28
**Status:** ✅ RESUELTO (ya implementado)
```python
self.model = "gpt-3.5-turbo"  # Disponible para todos los usuarios
```

### "RateLimitError: Error code: 429 - insufficient_quota" 
**Problema:** Tu cuenta OpenAI no tiene crédito o ha excedido su cuota
**Síntomas:**
```
HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 429 Too Many Requests"
Error: insufficient_quota
```
**Solución:**
1. Ir a https://platform.openai.com/account/billing/overview
2. Verificar que tengas método de pago agregado
3. Asegurarse que tu plan esté activo
4. Agregar crédito si es necesario

**Status:** ✅ MITIGADO (2026-05-29)
- Se implementó **fallback automático**: `_generate_fallback_response()`
- Cuando OpenAI devuelve 429, sistema genera respuesta simulada realista
- Permite seguir testeando UI sin bloqueos
- Log: `⚠️  [AGENT] OpenAI quota excedida - usando respuesta fallback`
- Una vez agregues crédito, sistema usará OpenAI real automáticamente

### "ValueError: OPENAI_API_KEY no está configurada"
→ Falta agregar clave en `.env`
→ Solución: Copiar clave desde https://platform.openai.com/api-keys

### "Connection timeout - OpenAI"
→ Error de red
→ Verificar conexión internet
→ Reintentar en 10s

### Chat muy lento (>10s)
→ OpenAI puede estar saturado
→ Normal durante horario pico
→ `gpt-3.5-turbo` es más rápido que `gpt-4`

---

## 📊 Métricas a Monitorear

- Tiempo promedio de respuesta (target: <3s)
- Tokens utilizados por request (avg: ~200)
- Costo por mes (GPT-4: ~$0.05 por 1K tokens)
- Errores de API (mantener <1%)

---

**Mantener actualizado este documento conforme avancemos con:**
- Bugs encontrados y soluciones
- Cambios de prompt system
- Optimizaciones de rendimiento
- Feedback del usuario
