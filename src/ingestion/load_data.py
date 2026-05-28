import os
import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
from faker import Faker
from dotenv import load_dotenv
from supabase import create_client, Client

# =====================================================================
# CONFIGURACIÓN — Las credenciales van en un archivo .env, NUNCA aquí.
# Crea un archivo .env en la raíz del proyecto con este contenido:
#   SUPABASE_URL=https://tu-proyecto.supabase.co
#   SUPABASE_KEY=tu-service-role-key
# =====================================================================
load_dotenv()

SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise EnvironmentError(
        "Faltan variables de entorno. Crea un archivo .env con SUPABASE_URL y SUPABASE_KEY."
    )

fake = Faker(['es_ES'])
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =====================================================================
# CONSTANTES
# =====================================================================
CANTIDAD_ASEGURADOS: int = 150
CANTIDAD_PROVEEDORES: int = 20

COBERTURAS: List[str] = ["Vehículos Livianos", "Vehículos Pesados", "Todo Riesgo Automotriz"]
TIPOS_PROVEEDORES: List[str] = ["Taller Mecánico", "Perito Automotriz", "Centro de Colisión"]
DOCUMENTOS_TIPOS: List[str] = ["Factura de Reparación", "Informe de Peritaje", "Copia de Cédula"]

NARRATIVAS_NORMALES: List[str] = [
    "El asegurado reporta un choque leve estacionado en el supermercado, daños en el parachoques trasero.",
    "Pérdida de control en vía mojada perdiendo pista e impactando contra baranda de seguridad lateral.",
    "Colisión lateral en intersección regulada por semáforo por conductor que no respeta el disco Pare.",
    "Rotura de parabrisas delantero por impacto de piedra saltada de un camión en la carretera principal.",
    "El cliente indica que al regresar a su vehículo estacionado encontró la ventana lateral rota y faltaban accesorios."
]

NARRATIVA_FRAUDE_CLONADA: str = (
    "El vehículo transitaba a 40km/h por la calle secundaria cuando un camión no identificado "
    "frena abruptamente, impactándolo en el costado izquierdo antes de darse a la fuga sin dejar rastros."
)

# =====================================================================
# GENERADOR DE EMBEDDINGS SIMULADOS
# Sin dependencia de numpy — lógica de normalización manual.
# En producción, reemplazar por embeddings reales (OpenAI, Claude, etc.)
# =====================================================================
def simular_vector_embedding() -> List[float]:
    """Genera un vector aleatorio normalizado de 1536 dimensiones."""
    vector = [random.gauss(0, 1) for _ in range(1536)]
    norma = sum(x ** 2 for x in vector) ** 0.5
    return [x / norma for x in vector]

# =====================================================================
# ORQUESTADOR DE GENERACIÓN DE DATOS
# =====================================================================
class DataGenerator:
    def __init__(self):
        self.asegurados_ids: List[str] = []
        self.polizas_ids: List[str] = []
        self.polizas_fechas: Dict[str, datetime] = {}
        self.proveedores_ids: List[str] = []
        self.siniestros_ids: List[str] = []
        self.taller_sospechoso_id: str = ""

    def borrar_datos_existentes(self) -> None:
        """
        Limpia las tablas en orden inverso de claves foráneas.
        Usa una condición que funciona en TODAS las tablas, sin depender
        de nombres de columna distintos por tabla.
        """
        print("Limpiando tablas de Supabase...")
        # Eliminamos todos los registros usando una fecha muy antigua como ancla.
        # Cada tabla sí tiene 'fecha_registro' o usamos .gte con su PK.
        # La forma más universal en Supabase es usar .neq con un valor imposible
        # sobre la columna correcta de cada tabla.
        tablas_y_pk = {
            "documentos":  "id_documento",
            "siniestros":  "id_siniestro",
            "proveedores": "id_proveedor",
            "polizas":     "id_poliza",
            "asegurados":  "id_asegurado",
        }
        for tabla, pk in tablas_y_pk.items():
            try:
                # Borra todos los registros cuyo PK no sea el string vacío
                # (es decir, todos, porque ningún ID real es "").
                supabase.table(tabla).delete().neq(pk, "").execute()
                print(f"  ✓ Tabla '{tabla}' limpiada.")
            except Exception as e:
                print(f"  ⚠️ Nota al limpiar '{tabla}' (puede estar vacía): {e}")

    def generar_asegurados(self) -> None:
        print(f"Generando {CANTIDAD_ASEGURADOS} Asegurados...")
        batch: List[Dict[str, Any]] = []
        for _ in range(CANTIDAD_ASEGURADOS):
            uid = f"ase-{uuid.uuid4().hex[:8]}"
            self.asegurados_ids.append(uid)
            batch.append({
                "id_asegurado": uid,
                "nombre_completo": fake.name(),
                "documento_identidad": f"17{random.randint(10000000, 99999999)}",
                "telefono": f"09{random.randint(80000000, 99999999)}",
                "correo_electronico": fake.email(),
                "fecha_registro": (datetime.now() - timedelta(days=random.randint(100, 500))).isoformat()
            })
        supabase.table("asegurados").insert(batch).execute()

    def generar_polizas(self) -> None:
        print("Generando Pólizas vinculadas...")
        batch: List[Dict[str, Any]] = []
        for id_aseg in self.asegurados_ids:
            uid = f"pol-{uuid.uuid4().hex[:8]}"
            fecha_inicio = datetime.now() - timedelta(days=random.randint(1, 90))
            fecha_fin = fecha_inicio + timedelta(days=365)

            self.polizas_ids.append(uid)
            self.polizas_fechas[uid] = fecha_inicio

            batch.append({
                "id_poliza": uid,
                "id_asegurado": id_aseg,
                "numero_poliza": f"POL-{random.randint(100000, 999999)}",
                "fecha_inicio_vigencia": fecha_inicio.isoformat(),
                "fecha_fin_vigencia": fecha_fin.isoformat(),
                "monto_asegurado": float(random.randint(12000, 45000)),
                "tipo_cobertura": random.choice(COBERTURAS),
                "estado_poliza": "Activa"
            })
        supabase.table("polizas").insert(batch).execute()

    def generar_proveedores(self) -> None:
        print(f"Generando {CANTIDAD_PROVEEDORES} Proveedores...")
        batch: List[Dict[str, Any]] = []
        for i in range(CANTIDAD_PROVEEDORES):
            uid = f"prov-{uuid.uuid4().hex[:8]}"
            self.proveedores_ids.append(uid)

            if i == 0:
                # FIX: El taller sospechoso se crea directamente con lista_restrictiva=True.
                # Antes se creaba en False y nunca se actualizaba, por lo que
                # evaluar_proveedor() en fraud_rules.py nunca disparaba los 50 puntos.
                self.taller_sospechoso_id = uid
                nombre = "TALLER COLISIÓN DEL SUR CIA. LTDA."
                es_restrictivo = True
                tipo = "Taller Mecánico"
            else:
                nombre = f"{random.choice(['Taller', 'Autocentro', 'Enderezada'])} {fake.last_name().upper()}"
                es_restrictivo = False
                tipo = random.choice(TIPOS_PROVEEDORES)

            batch.append({
                "id_proveedor": uid,
                "nombre_comercial": nombre,
                "ruc_cedula": f"179{random.randint(10000000, 99999999)}001",
                "tipo_proveedor": tipo,
                "lista_restrictiva": es_restrictivo  # ← Corrección crítica
            })
        supabase.table("proveedores").insert(batch).execute()

    def generar_siniestros(self) -> None:
        print("Generando Siniestros e inyectando patrones de fraude ocultos...")
        batch_siniestros: List[Dict[str, Any]] = []
        contador_siniestros = 1

        # --- CASOS NORMALES (85% del dataset) ---
        polizas_normales = self.polizas_ids[:int(len(self.polizas_ids) * 0.85)]
        for id_pol in polizas_normales:
            uid = f"sin-{uuid.uuid4().hex[:8]}"
            self.siniestros_ids.append(uid)

            fecha_poliza = self.polizas_fechas[id_pol]
            fecha_sin = fecha_poliza + timedelta(days=random.randint(20, 80))
            fecha_notif = fecha_sin + timedelta(days=random.randint(1, 3))

            batch_siniestros.append({
                "id_siniestro": uid,
                "id_poliza": id_pol,
                "id_proveedor": random.choice(self.proveedores_ids),
                "codigo_siniestro": f"SIN-2026-{contador_siniestros:04d}",
                "fecha_siniestro": fecha_sin.isoformat(),
                "fecha_notificacion": fecha_notif.isoformat(),
                "monto_reclamado": float(random.randint(300, 3500)),
                "descripcion_narrativa": random.choice(NARRATIVAS_NORMALES),
                "descripcion_embedding": simular_vector_embedding(),
                "estado_tramite": "En Revisión",
                "score_riesgo": 0,
                "semaforo_alerta": "Verde"
            })
            contador_siniestros += 1

        # --- FRAUDE 1: Borde de Vigencia (siniestro a las 3h de emitida la póliza) ---
        polizas_fraude_vigencia = self.polizas_ids[
            int(len(self.polizas_ids) * 0.85) : int(len(self.polizas_ids) * 0.90)
        ]
        for id_pol in polizas_fraude_vigencia:
            uid = f"sin-{uuid.uuid4().hex[:8]}"
            self.siniestros_ids.append(uid)

            fecha_poliza = self.polizas_fechas[id_pol]
            fecha_sin = fecha_poliza + timedelta(hours=3)   # ← Activa RF-01 (Crítico: +40 pts)
            fecha_notif = fecha_sin + timedelta(days=1)

            batch_siniestros.append({
                "id_siniestro": uid,
                "id_poliza": id_pol,
                "id_proveedor": random.choice(self.proveedores_ids),
                "codigo_siniestro": f"SIN-2026-{contador_siniestros:04d}",
                "fecha_siniestro": fecha_sin.isoformat(),
                "fecha_notificacion": fecha_notif.isoformat(),
                "monto_reclamado": float(random.randint(6000, 9500)),
                "descripcion_narrativa": (
                    "Iba manejando de noche camino a casa y perdí el control "
                    "golpeando la acera, dañando la mesa y el eje del carro."
                ),
                "descripcion_embedding": simular_vector_embedding(),
                "estado_tramite": "En Revisión",
                "score_riesgo": 0,
                "semaforo_alerta": "Verde"
            })
            contador_siniestros += 1

        # --- FRAUDE 2: Red de narrativas clonadas + proveedor crítico + demora ---
        # Activa RF-03 (+50 pts taller restrictivo), RF-04 (+30 pts demora), y similitud NLP
        polizas_fraude_red = self.polizas_ids[int(len(self.polizas_ids) * 0.90):]
        embedding_clon = simular_vector_embedding()  # Mismo embedding para toda la red

        for id_pol in polizas_fraude_red:
            uid = f"sin-{uuid.uuid4().hex[:8]}"
            self.siniestros_ids.append(uid)

            fecha_poliza = self.polizas_fechas[id_pol]
            fecha_sin = fecha_poliza + timedelta(days=15)
            fecha_notif = fecha_sin + timedelta(days=12)   # ← Activa RF-04 (+30 pts)

            batch_siniestros.append({
                "id_siniestro": uid,
                "id_poliza": id_pol,
                "id_proveedor": self.taller_sospechoso_id,  # ← Activa RF-03 (+50 pts)
                "codigo_siniestro": f"SIN-2026-{contador_siniestros:04d}",
                "fecha_siniestro": fecha_sin.isoformat(),
                "fecha_notificacion": fecha_notif.isoformat(),
                "monto_reclamado": float(random.randint(4000, 5000)),
                "descripcion_narrativa": NARRATIVA_FRAUDE_CLONADA,
                "descripcion_embedding": embedding_clon,
                "estado_tramite": "En Revisión",
                "score_riesgo": 0,
                "semaforo_alerta": "Verde"
            })
            contador_siniestros += 1

        supabase.table("siniestros").insert(batch_siniestros).execute()

    def generar_documentos(self) -> None:
        print("Vinculando Documentos Analíticos a los Siniestros...")
        batch: List[Dict[str, Any]] = []
        for id_sin in self.siniestros_ids:
            for _ in range(random.randint(1, 3)):
                uid = f"doc-{uuid.uuid4().hex[:8]}"
                es_sospechoso = random.random() < 0.05

                batch.append({
                    "id_documento": uid,
                    "id_siniestro": id_sin,
                    "tipo_documento": random.choice(DOCUMENTOS_TIPOS),
                    "url_archivo": (
                        f"https://tu-bucket.supabase.co/storage/v1/object/public/claims/{uid}.pdf"
                    ),
                    "fecha_carga": datetime.now().isoformat(),
                    "es_legible": not es_sospechoso,
                    "posible_adulteracion": es_sospechoso
                })
        supabase.table("documentos").insert(batch).execute()


# =====================================================================
# FLUJO PRINCIPAL
# =====================================================================
if __name__ == "__main__":
    print("INICIANDO INGESTIÓN INTELIGENTE DE DATOS SINTÉTICOS")

    generator = DataGenerator()

    generator.borrar_datos_existentes()
    generator.generar_asegurados()
    generator.generar_polizas()
    generator.generar_proveedores()
    generator.generar_siniestros()
    generator.generar_documentos()

    print("\n¡PROCESO COMPLETADO CON ÉXITO!")
    print("La base de datos está poblada y lista para auditar.")
    print(f"→ ID del Taller Crítico (lista restrictiva): {generator.taller_sospechoso_id}")