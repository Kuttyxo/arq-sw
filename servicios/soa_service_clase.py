import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from soa_lib import connect_to_bus, send_message, receive_message
import json
import uuid
from datetime import datetime

NOMBRE_SERVICIO = "clase"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCHIVO_CLASES = os.path.join(BASE_DIR, "data", "clases.json")

def cargar_clases():
    if not os.path.exists(ARCHIVO_CLASES):
        return []
    with open(ARCHIVO_CLASES, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_clases(clases):
    os.makedirs(os.path.dirname(ARCHIVO_CLASES), exist_ok=True)
    with open(ARCHIVO_CLASES, "w", encoding="utf-8") as f:
        json.dump(clases, f, indent=2, ensure_ascii=False)

def crear_clase(datos):
    campos = ["disciplina", "rut_profe", "fecha", "hora", "cupos_max"]
    for c in campos:
        if c not in datos:
            return {"ok": False, "error": f"Falta el campo '{c}'"}

    try:
        cupos_max = int(datos["cupos_max"])
        if cupos_max <= 0:
            return {"ok": False, "error": "cupos_max debe ser mayor a 0"}
    except ValueError:
        return {"ok": False, "error": "cupos_max debe ser un numero entero"}

    try:
        datetime.strptime(datos["fecha"], "%Y-%m-%d")
    except ValueError:
        return {"ok": False, "error": "Formato de fecha invalido. Use YYYY-MM-DD"}

    try:
        datetime.strptime(datos["hora"], "%H:%M")
    except ValueError:
        return {"ok": False, "error": "Formato de hora invalido. Use HH:MM"}

    clases = cargar_clases()
    nueva = {
        "id_clase": str(uuid.uuid4())[:8],
        "disciplina": datos["disciplina"],
        "rut_profe": datos["rut_profe"],
        "fecha": datos["fecha"],
        "hora": datos["hora"],
        "cupos_max": cupos_max,
        "cupos_disponibles": cupos_max,
        "alumnos_inscritos": []
    }
    clases.append(nueva)
    guardar_clases(clases)
    print(f"  → Clase creada: {nueva['id_clase']} | {nueva['disciplina']} | {nueva['fecha']} {nueva['hora']}")
    return {"ok": True, "id_clase": nueva["id_clase"]}

def listar_clases(datos):
    clases = cargar_clases()
    fecha_filtro = datos.get("fecha")

    if fecha_filtro:
        clases = [c for c in clases if c["fecha"] == fecha_filtro]

    resultado = []
    for c in clases:
        resultado.append({
            "id_clase": c["id_clase"],
            "disciplina": c["disciplina"],
            "rut_profe": c["rut_profe"],
            "fecha": c["fecha"],
            "hora": c["hora"],
            "cupos_max": c["cupos_max"],
            "cupos_disponibles": c["cupos_disponibles"]
        })

    return {"ok": True, "clases": resultado}

def obtener_clase(datos):
    if "id_clase" not in datos:
        return {"ok": False, "error": "Falta el campo 'id_clase'"}

    clases = cargar_clases()
    for c in clases:
        if c["id_clase"] == datos["id_clase"]:
            return {"ok": True, "clase": c}

    return {"ok": False, "error": f"Clase '{datos['id_clase']}' no encontrada"}

def actualizar_cupo(datos):
    if "id_clase" not in datos or "delta" not in datos:
        return {"ok": False, "error": "Faltan campos 'id_clase' o 'delta'"}

    try:
        delta = int(datos["delta"])
        if delta not in (1, -1):
            return {"ok": False, "error": "delta debe ser 1 o -1"}
    except ValueError:
        return {"ok": False, "error": "delta debe ser un numero entero"}

    clases = cargar_clases()
    for c in clases:
        if c["id_clase"] == datos["id_clase"]:
            nuevo_cupo = c["cupos_disponibles"] + delta
            if nuevo_cupo < 0:
                return {"ok": False, "error": "No hay cupos disponibles"}
            if nuevo_cupo > c["cupos_max"]:
                return {"ok": False, "error": "Los cupos no pueden superar el maximo"}

            c["cupos_disponibles"] = nuevo_cupo

            rut_alumno = datos.get("rut_alumno")
            if rut_alumno:
                if delta == -1:
                    if rut_alumno not in c["alumnos_inscritos"]:
                        c["alumnos_inscritos"].append(rut_alumno)
                elif delta == 1:
                    if rut_alumno in c["alumnos_inscritos"]:
                        c["alumnos_inscritos"].remove(rut_alumno)

            guardar_clases(clases)
            print(f"  → Cupo actualizado: clase {c['id_clase']} | cupos_disp={nuevo_cupo}")
            return {"ok": True, "cupos_disponibles": nuevo_cupo}

    return {"ok": False, "error": f"Clase '{datos['id_clase']}' no encontrada"}

ACCIONES = {
    "crear_clase": crear_clase,
    "listar_clases": listar_clases,
    "obtener_clase": obtener_clase,
    "actualizar_cupo": actualizar_cupo,
}

def procesar(payload_str):
    try:
        datos = json.loads(payload_str)
    except json.JSONDecodeError:
        return json.dumps({"ok": False, "error": "JSON invalido"})

    accion = datos.get("accion")
    if not accion:
        return json.dumps({"ok": False, "error": "Falta el campo 'accion'"})

    handler = ACCIONES.get(accion)
    if not handler:
        return json.dumps({"ok": False, "error": f"Accion desconocida: '{accion}'"})

    try:
        resultado = handler(datos)
        return json.dumps(resultado, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"ok": False, "error": f"Error interno: {str(e)}"})

sock = connect_to_bus()

try:
    print(f"Registrando servicio '{NOMBRE_SERVICIO}'...")
    send_message(sock, "sinit", NOMBRE_SERVICIO)
    init_data = receive_message(sock)
    print(f"Confirmacion del bus: {init_data!r}")
    print(f"Servicio '{NOMBRE_SERVICIO}' listo.\n")

    while True:
        data = receive_message(sock)
        if not data:
            print("Conexion cerrada por el bus.")
            break

        payload = data[5:].decode()
        print(f"[clase] Solicitud recibida: {payload}")

        respuesta = procesar(payload)
        send_message(sock, NOMBRE_SERVICIO, respuesta)
        print(f"[clase] Respuesta enviada: {respuesta}\n")

except Exception as e:
    print(f"Error en el servicio: {e}")
finally:
    print("Cerrando socket del servicio 'clase'")
    sock.close()