# Uso de IA — A.U.R.A (alineado al PDF del hackathon)

## Enfoque híbrido (3 capas + combinación)

| Capa | Módulo | Qué hace | Entra al score final |
|------|--------|----------|----------------------|
| **NLP** | `src/nlp/narrative_similarity.py` | Similitud de narrativas (embeddings + cruce asegurado/proveedor) | Solo vía **reglas** (RF-07) |
| **Reglas** | `src/rules/fraud_rules.py` | RF-05…RF-07, docs, montos, vigencia… | Hasta **70 pts** |
| **ML** | `src/models/fraud_model.py` | LogisticRegression tabular (sin NLP) | Hasta **20 pts** |
| **Anomalías** | `src/models/anomaly_model.py` | IsolationForest | Hasta **10 pts** |

**Score final** = 70% reglas + 20% ML + 10% anomalías → semáforo VERDE / AMARILLO / ROJO.

## Por qué NLP no está dentro del ML

El PDF (§9) lista por separado:

- Machine Learning supervisado
- Procesamiento de lenguaje natural
- Reglas de negocio

Por eso `max_similitud_narrativa` **no** es feature del modelo `.joblib`; alimenta **RF-07** en reglas.

## Parámetros de prod (notebook 03)

Guardados en `data/processed/fraud_model_config.json`:

- **Modelo**: LogisticRegression, **C=0.1**
- **Threshold ML** (alerta binaria): **0.7** (umbral operativo notebook 03; fijo en prod)
- El **score_final** híbrido sigue usando `ml_proba` continua (0–20 pts), no el threshold.

## Comandos

```bash
python scripts/train_fraud_model.py   # fraud_lr.joblib + config + fraud_iso.joblib
python scripts/run_scoring.py         # NLP → reglas → ML → anomalías → CSV scored
```
