import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from soa_lib import connect_to_bus, send_message, receive_message
import json
from datetime import datetime

NOMBRE_SERVICIO = "notif"

RUTA_DATOS = os.path.join(os.path.dirname(__file__), "..", "data", "notificaciones.json")


def cargar_notificaciones():
    try:
        with open(RUTA_DATOS, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def guardar_notificaciones(notificaciones):
    os.makedirs(os.path.dirname(RUTA_DATOS), exist_ok=True)
    with open(RUTA_DATOS, "w", encoding="utf-8") as f:
        json.dump(notificaciones, f, indent=2, ensure_ascii=False)


def siguiente_id(notificaciones):
    maximo = 0
    for n in notificaciones:
        nid = str(n.get("id", ""))
        if nid.startswith("notif_") and nid[6:].isdigit():
            maximo = max(maximo, int(nid[6:]))
    return f"notif_{maximo + 1}"


def accion_enviar(datos):
    rut_destino = datos.get("rut_destino")
    tipo = datos.get("tipo")
    mensaje = datos.get("mensaje")
    if not rut_destino or not tipo or not mensaje:
        return {"ok": False, "error": "Faltan parametros: rut_destino, tipo, mensaje"}
    notificaciones = cargar_notificaciones()
    notificacion = {
        "id": siguiente_id(notificaciones),
        "rut_destino": rut_destino,
        "tipo": tipo,
        "mensaje": mensaje,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "pendiente": True,
    }
    notificaciones.append(notificacion)
    guardar_notificaciones(notificaciones)
    print(f"[NOTIFICACION] -> {rut_destino} ({tipo}): {mensaje}")
    return {"ok": True}


def accion_listar_pendientes(datos):
    rut_destino = datos.get("rut_destino")
    if not rut_destino:
        return {"ok": False, "error": "Falta parametro: rut_destino"}
    notificaciones = cargar_notificaciones()
    pendientes = [
        n for n in notificaciones
        if n.get("rut_destino") == rut_destino and n.get("pendiente")
    ]
    return {"ok": True, "notificaciones": pendientes}


def procesar(datos_json):
    try:
        datos = json.loads(datos_json)
    except json.JSONDecodeError:
        return json.dumps({"ok": False, "error": "JSON invalido"})

    accion = datos.get("accion")
    if accion == "enviar":
        return json.dumps(accion_enviar(datos))
    if accion == "listar_pendientes":
        return json.dumps(accion_listar_pendientes(datos))
    return json.dumps({"ok": False, "error": "Accion desconocida"})


sock = connect_to_bus()
try:
    send_message(sock, "sinit", NOMBRE_SERVICIO)
    init_data = receive_message(sock)
    print(f"Servicio '{NOMBRE_SERVICIO}' registrado: {init_data!r}")
    while True:
        data = receive_message(sock)
        if not data:
            break
        # CORRECCION: usar data[10:] en lugar de data[5:]
        payload = data[10:].decode()
        print(f"Peticion recibida: {payload}")
        respuesta = procesar(payload)
        send_message(sock, NOMBRE_SERVICIO, respuesta)
        print(f"Respuesta enviada: {respuesta}")
except Exception as e:
    print(f"Error: {e}")
finally:
    sock.close()