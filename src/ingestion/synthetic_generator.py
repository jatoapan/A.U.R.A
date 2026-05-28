from __future__ import annotations

import math
import random
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

import numpy as np
from faker import Faker
from sentence_transformers import SentenceTransformer

from .config import IngestionConfig


PROVINCIAS_IDS: List[str] = [
    "17",
    "09",
    "01",
    "13",
    "11",
    "18",
    "07",
    "12",
    "06",
]  # Pichincha, Guayas, Azuay, Manabí, Loja, Tungurahua, El Oro, Los Ríos, Chimborazo

COBERTURAS: List[str] = ["VEHÍCULOS LIVIANOS", "VEHÍCULOS PESADOS", "TODO RIESGO AUTOMOTRIZ"]
TIPOS_PROVEEDORES: List[str] = ["TALLER MECÁNICO", "PERITO AUTOMOTRIZ", "CENTRO DE COLISIÓN"]
DOCUMENTOS_TIPOS: List[str] = ["FACTURA DE REPARACIÓN", "INFORME DE PERITAJE", "COPIA DE CÉDULA"]
COBERTURAS_SINIESTRO: List[str] = ["CHOQUE", "ROBO", "DAÑOS"]

SUCURSALES: List[str] = ["GUAYAQUIL", "QUITO", "CUENCA", "MANTA"]
CAUSAS_RIESGO: List[str] = ["VEHÍCULOS"]

CIUDADES_EC: List[str] = ["QUITO", "GUAYAQUIL", "CUENCA", "MANTA", "AMBATO", "LOJA", "PORTOVIEJO"]
VIAS: List[str] = [
    "AVENIDA PRINCIPAL",
    "CALLE SECUNDARIA",
    "VÍA PERIMETRAL",
    "AUTOPISTA",
    "VÍA RÁPIDA",
    "INTERSECCIÓN",
]
CONDICIONES: List[str] = ["LLUVIA", "NEBLINA", "CALZADA MOJADA", "NOCHE", "MADRUGADA", "TRÁFICO PESADO", "PAVIMENTO IRREGULAR"]
PIEZAS: List[str] = ["PARACHOQUES DELANTERO", "PARACHOQUES TRASERO", "PUERTA", "GUARDAFANGO", "FARO", "CAPÓ", "PARABRISAS"]
ACTORES: List[str] = ["CAMIÓN", "MOTO", "TAXI", "BUS", "CAMIONETA", "AUTO PARTICULAR"]
LUGARES: List[str] = ["SUPERMERCADO", "CENTRO COMERCIAL", "GASOLINERA", "PARQUEADERO", "VÍA PÚBLICA", "DOMICILIO"]
ACCIONES: List[str] = ["FRENA ABRUPTAMENTE", "SE CAMBIA DE CARRIL", "NO RESPETA EL PARE", "SE PASA EL SEMÁFORO", "RETROCEDE SIN PRECAUCIÓN"]

PLANTILLAS_CHOQUE: List[str] = [
    "EN {CIUDAD}, EL VEHÍCULO CIRCULABA POR {VIA} EN CONDICIÓN {COND}. {TERCERO} {ACCION} Y SE PRODUCE {TIPO_IMPACTO}. SE REPORTAN DAÑOS EN {PIEZA}.",
    "SINIESTRO EN {CIUDAD} CERCA DE {LUGAR}. EL ASEGURADO INDICA {ACCION} DEL {TERCERO} Y UN {TIPO_IMPACTO}. DAÑOS VISIBLES EN {PIEZA} Y {PIEZA2}.",
]

PLANTILLAS_ROBO: List[str] = [
    "EL ASEGURADO REPORTA ROBO EN {CIUDAD} EN {LUGAR}. AL REGRESAR ENCUENTRA {EVIDENCIA}. FALTAN {ITEMS_ROBO}.",
    "ROBO REPORTADO EN {CIUDAD}. OCURRE EN {LUGAR} DURANTE {COND}. SE INDICA {EVIDENCIA} Y SUSTRACCIÓN DE {ITEMS_ROBO}.",
]

PLANTILLAS_DANOS: List[str] = [
    "DAÑO ACCIDENTAL EN {CIUDAD}: IMPACTO DE OBJETO EN {PIEZA}. OCURRE EN {VIA} CON {COND}.",
    "EL CLIENTE REPORTA DAÑOS EN {PIEZA} EN {CIUDAD} EN {LUGAR}. NO IDENTIFICA TERCERO. CONDICIÓN {COND}.",
]

EVIDENCIAS_ROBO: List[str] = ["VIDRIO LATERAL ROTO", "CERRADURA FORZADA", "PUERTA ENTREABIERTA", "SEÑALES DE PALANQUEO"]
ITEMS_ROBO: List[str] = ["RADIO", "COMPUTADORA PORTÁTIL", "HERRAMIENTAS", "LLANTAS", "BATERÍA", "ESPEJOS"]
TIPOS_IMPACTO: List[str] = ["COLISIÓN FRONTAL LEVE", "COLISIÓN LATERAL", "IMPACTO POSTERIOR", "CHOQUE EN INTERSECCIÓN"]

NARRATIVA_FRAUDE_BASE: str = (
    "EL VEHÍCULO TRANSITABA A 40 KM/H POR LA CALLE SECUNDARIA CUANDO UN CAMIÓN NO IDENTIFICADO "
    "FRENA ABRUPTAMENTE E IMPACTA EL COSTADO IZQUIERDO; LUEGO SE DA A LA FUGA SIN DEJAR RASTROS."
)


@dataclass(frozen=True)
class GeneratedData:
    asegurados: List[Dict[str, Any]]
    polizas: List[Dict[str, Any]]
    proveedores: List[Dict[str, Any]]
    siniestros: List[Dict[str, Any]]
    documentos: List[Dict[str, Any]]
    taller_critico_id: str


def _generar_narrativa(cfg: IngestionConfig, cobertura: str, es_fraude: bool) -> str:
    if es_fraude and random.random() < cfg.narrative_clone_prob:
        ciudad = random.choice(CIUDADES_EC)
        pieza = random.choice(PIEZAS)
        lugar = random.choice(LUGARES)
        return f"{NARRATIVA_FRAUDE_BASE} OCURRE EN {ciudad} CERCA DE {lugar}. DAÑOS EN {pieza}."

    ciudad = random.choice(CIUDADES_EC)
    via = random.choice(VIAS)
    cond = random.choice(CONDICIONES)
    pieza = random.choice(PIEZAS)
    pieza2 = random.choice([p for p in PIEZAS if p != pieza])
    tercero = random.choice(ACTORES)
    accion = random.choice(ACCIONES)
    lugar = random.choice(LUGARES)
    tipo_impacto = random.choice(TIPOS_IMPACTO)
    evidencia = random.choice(EVIDENCIAS_ROBO)
    items_robo = ", ".join(random.sample(ITEMS_ROBO, k=random.randint(1, 3)))

    if cobertura == "CHOQUE":
        plantilla = random.choice(PLANTILLAS_CHOQUE)
        return plantilla.format(
            CIUDAD=ciudad,
            VIA=via,
            COND=cond,
            TERCERO=tercero,
            ACCION=accion,
            TIPO_IMPACTO=tipo_impacto,
            PIEZA=pieza,
            PIEZA2=pieza2,
            LUGAR=lugar,
        )

    if cobertura == "ROBO":
        plantilla = random.choice(PLANTILLAS_ROBO)
        return plantilla.format(
            CIUDAD=ciudad,
            LUGAR=lugar,
            COND=cond,
            EVIDENCIA=evidencia,
            ITEMS_ROBO=items_robo,
        )

    plantilla = random.choice(PLANTILLAS_DANOS)
    return plantilla.format(CIUDAD=ciudad, VIA=via, COND=cond, PIEZA=pieza, LUGAR=lugar)


def _generar_monto_reclamado(cobertura: str, es_fraude: bool) -> float:
    if cobertura == "ROBO":
        base = random.randint(1500, 9000)
    elif cobertura == "CHOQUE":
        base = random.randint(300, 6000)
    else:
        base = random.randint(150, 2500)

    factor = random.uniform(1.10, 1.60) if es_fraude else random.uniform(0.85, 1.15)
    return float(round(base * factor, 2))


def generate_synthetic_data(cfg: IngestionConfig) -> GeneratedData:
    random.seed(cfg.seed)
    np.random.seed(cfg.seed)
    Faker.seed(cfg.seed)

    fake = Faker(["es_ES"])
    model = SentenceTransformer("all-MiniLM-L6-v2")  # 384 dims

    def embed(texto: str) -> List[float]:
        return model.encode(texto).tolist()

    asegurados_ids: List[str] = []
    polizas_ids: List[str] = []
    polizas_fechas: Dict[str, Tuple[datetime, datetime]] = {}
    polizas_asegurado: Dict[str, str] = {}
    proveedores_ids: List[str] = []
    proveedores_sospechosos_ids: List[str] = []
    siniestros_ids: List[str] = []
    taller_critico_id = ""

    asegurados: List[Dict[str, Any]] = []
    for _ in range(cfg.n_asegurados):
        uid = f"ase-{uuid.uuid4().hex[:8]}"
        asegurados_ids.append(uid)

        nombre = f"{fake.first_name()} {fake.first_name()} {fake.last_name()} {fake.last_name()}".upper()
        prefix = random.choice(PROVINCIAS_IDS)
        cedula = f"{prefix}{random.randint(10000000, 99999999)}"
        asegurados.append(
            {
                "id_asegurado": uid,
                "nombre_completo": nombre,
                "documento_identidad": cedula,
                "telefono": f"09{random.randint(80000000, 99999999)}",
                "correo_electronico": fake.email(),
                "fecha_registro": (datetime.now() - timedelta(days=random.randint(100, 500))).isoformat(),
            }
        )

    polizas: List[Dict[str, Any]] = []
    for id_aseg in asegurados_ids:
        uid = f"pol-{uuid.uuid4().hex[:8]}"
        fecha_inicio = datetime.now() - timedelta(days=random.randint(1, 90))
        fecha_fin = fecha_inicio + timedelta(days=365)

        polizas_ids.append(uid)
        polizas_fechas[uid] = (fecha_inicio, fecha_fin)
        polizas_asegurado[uid] = id_aseg

        numero_poliza = f"POL-{uuid.uuid4().hex[:12].upper()}"

        polizas.append(
            {
                "id_poliza": uid,
                "id_asegurado": id_aseg,
                "numero_poliza": numero_poliza,
                "ramo": "VEHICULOS",
                "fecha_inicio_vigencia": fecha_inicio.isoformat(),
                "fecha_fin_vigencia": fecha_fin.isoformat(),
                "monto_asegurado": float(random.randint(12000, 45000)),
                "tipo_cobertura": random.choice(COBERTURAS).upper(),
                "estado_poliza": "ACTIVA",
            }
        )

    proveedores: List[Dict[str, Any]] = []
    objetivo = int(math.ceil(cfg.n_proveedores * cfg.suspect_provider_rate))
    n_sospechosos = max(cfg.suspect_provider_min, min(cfg.suspect_provider_max, min(cfg.n_proveedores, objetivo)))
    suspect_indices = set(random.sample(range(cfg.n_proveedores), k=n_sospechosos)) if cfg.n_proveedores > 0 else set()
    idx_restrictivo = min(suspect_indices) if suspect_indices else 0

    for i in range(cfg.n_proveedores):
        uid = f"prov-{uuid.uuid4().hex[:8]}"
        proveedores_ids.append(uid)

        prefix = random.choice(PROVINCIAS_IDS)
        ruc = f"{prefix}9{random.randint(1000000, 9999999)}001"

        if i in suspect_indices:
            proveedores_sospechosos_ids.append(uid)
            nombre = random.choice(
                [
                    "TALLER COLISIÓN DEL SUR CIA. LTDA.",
                    "AUTOCENTRO EL PACÍFICO S.A.",
                    "ENDEREZADA Y PINTURA ANDES",
                    "TALLER RÁPIDO LA 9 DE OCTUBRE",
                ]
            )
            es_restrictive = i == idx_restrictivo
            tipo = "TALLER MECÁNICO"
            if es_restrictive:
                taller_critico_id = uid
        else:
            nombre = f"{random.choice(['TALLER', 'AUTOCENTRO', 'ENDEREZADA'])} {fake.last_name().upper()}"
            es_restrictive = False
            tipo = random.choice(TIPOS_PROVEEDORES).upper()

        proveedores.append(
            {
                "id_proveedor": uid,
                "nombre_comercial": nombre,
                "ruc_cedula": ruc,
                "tipo_proveedor": tipo,
                "lista_restrictiva": es_restrictive,
            }
        )

    siniestros: List[Dict[str, Any]] = []
    contador_siniestros = 1
    for id_pol in polizas_ids:
        es_fraude = random.random() < cfg.fraud_rate
        uid = f"sin-{uuid.uuid4().hex[:8]}"
        siniestros_ids.append(uid)

        fecha_inicio, fecha_fin = polizas_fechas[id_pol]
        if es_fraude and random.random() < cfg.fraud_near_start_prob:
            fecha_sin = fecha_inicio + timedelta(days=random.randint(0, cfg.near_start_days_max))
            if random.random() < cfg.fraud_late_report_prob:
                fecha_notif = fecha_sin + timedelta(days=random.randint(cfg.late_report_days_min, cfg.late_report_days_max))
            else:
                fecha_notif = fecha_sin + timedelta(days=random.randint(cfg.normal_report_days_min, cfg.normal_report_days_max))
        else:
            fecha_sin = fecha_inicio + timedelta(days=random.randint(cfg.normal_days_since_start_min, cfg.normal_days_since_start_max))
            fecha_notif = fecha_sin + timedelta(days=random.randint(cfg.normal_report_days_min, cfg.normal_report_days_max))

        if es_fraude and proveedores_sospechosos_ids and random.random() < cfg.fraud_to_suspect_prob:
            id_prov = random.choice(proveedores_sospechosos_ids)
        else:
            if proveedores_sospechosos_ids and random.random() < cfg.normal_to_suspect_prob:
                id_prov = random.choice(proveedores_sospechosos_ids)
            else:
                id_prov = random.choice(proveedores_ids)

        cobertura = random.choices(
            population=COBERTURAS_SINIESTRO,
            weights=[cfg.coverage_weight_choque, cfg.coverage_weight_robo, cfg.coverage_weight_danos],
            k=1,
        )[0]
        narrativa = _generar_narrativa(cfg=cfg, cobertura=cobertura, es_fraude=es_fraude)
        embedding = embed(narrativa)
        monto_reclamado = _generar_monto_reclamado(cobertura=cobertura, es_fraude=es_fraude)

        if cobertura == "ROBO":
            docs_completos = random.random() < (cfg.docs_complete_prob_fraud_robo if es_fraude else cfg.docs_complete_prob_normal_robo)
        else:
            docs_completos = random.random() < (cfg.docs_complete_prob_fraud_no_robo if es_fraude else cfg.docs_complete_prob_normal_no_robo)

        historial = (
            random.randint(cfg.history_fraud_min, cfg.history_fraud_max)
            if (es_fraude and random.random() < cfg.fraud_high_history_prob)
            else random.randint(cfg.history_normal_min, cfg.history_normal_max)
        )

        siniestros.append(
            {
                "id_siniestro": uid,
                "id_poliza": id_pol,
                "id_asegurado": polizas_asegurado[id_pol],
                "id_proveedor": id_prov,
                "codigo_siniestro": f"SIN-2026-{contador_siniestros:04d}",
                "ramo": "VEHICULOS",
                "cobertura": cobertura,
                "fecha_ocurrencia": fecha_sin.isoformat(),
                "fecha_reporte": fecha_notif.isoformat(),
                "monto_reclamado": monto_reclamado,
                "descripcion_narrativa": narrativa,
                "descripcion_embedding": embedding,
                "estado_tramite": "EN REVISION",
                "score_riesgo": 0,
                "semaforo_alerta": "VERDE",
                "causa_riesgo": random.choice(CAUSAS_RIESGO).upper(),
                "monto_estimado": round(monto_reclamado * random.uniform(cfg.monto_estimado_factor_min, cfg.monto_estimado_factor_max), 2),
                "monto_pagado": 0.0,
                "estado": "RESERVA",
                "sucursal": random.choice(SUCURSALES).upper(),
                "documentos_completos": docs_completos,
                "dias_desde_inicio_poliza": (fecha_sin - fecha_inicio).days,
                "dias_desde_fin_poliza": (fecha_fin - fecha_sin).days,
                "dias_entre_ocurrencia_reporte": (fecha_notif - fecha_sin).days,
                "historial_siniestros_asegurado": historial,
                "etiqueta_fraude_simulada": 1 if es_fraude else 0,
            }
        )
        contador_siniestros += 1

    documentos: List[Dict[str, Any]] = []
    for id_sin in siniestros_ids:
        for _ in range(random.randint(cfg.docs_per_claim_min, cfg.docs_per_claim_max)):
            uid = f"doc-{uuid.uuid4().hex[:8]}"
            es_sospechoso = random.random() < cfg.doc_suspicious_prob
            documentos.append(
                {
                    "id_documento": uid,
                    "id_siniestro": id_sin,
                    "tipo_documento": random.choice(DOCUMENTOS_TIPOS),
                    "url_archivo": f"https://tu-bucket.supabase.co/storage/v1/object/public/claims/{uid}.pdf",
                    "fecha_carga": datetime.now().isoformat(),
                    "es_legible": not es_sospechoso,
                    "posible_adulteracion": es_sospechoso,
                }
            )

    return GeneratedData(
        asegurados=asegurados,
        polizas=polizas,
        proveedores=proveedores,
        siniestros=siniestros,
        documentos=documentos,
        taller_critico_id=taller_critico_id,
    )

