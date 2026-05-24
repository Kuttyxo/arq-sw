import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from soa_lib import connect_to_bus, send_message, receive_message
import json

NOMBRE_SERVICIO = "profe"

RUTA_DATOS = os.path.join(os.path.dirname(__file__), "..", "data", "profesores.json")

def cargar_profesores():
    try:
        with open(RUTA_DATOS, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def guardar_profesores(profesores):
    os.makedirs(os.path.dirname(RUTA_DATOS), exist_ok=True)
    with open(RUTA_DATOS, "w", encoding="utf-8") as f:
        json.dump(profesores, f, indent=2, ensure_ascii=False)

def llamar_servicio(nombre_servicio, peticion, timeout=5):
    s = None
    try:
        s = connect_to_bus()
        s.settimeout(timeout)
        send_message(s, nombre_servicio, json.dumps(peticion))
        data = receive_message(s)
        if not data:
            return None
        cuerpo = data[5:].decode()
        return json.loads(cuerpo)
    except Exception:
        return None
    finally:
        if s is not None:
            s.close()

def accion_crear_profe(datos):
    rut = datos.get("rut")
    nombre = datos.get("nombre")
    especialidad = datos.get("especialidad")
    if not rut or not nombre or not especialidad:
        return {"ok": False, "error": "Faltan parametros: rut, nombre, especialidad"}
    profesores = cargar_profesores()
    if any(p.get("rut") == rut for p in profesores):
        return {"ok": False, "error": "RUT duplicado"}
    profesores.append({"rut": rut, "nombre": nombre, "especialidad": especialidad})
    guardar_profesores(profesores)
    return {"ok": True}

def accion_listar_profes():
    return {"ok": True, "profesores": cargar_profesores()}

def accion_asistencia(datos):
    id_clase = datos.get("id_clase")
    if not id_clase:
        return {"ok": False, "error": "Falta parametro: id_clase"}

    resp_reser = llamar_servicio("reser", {"accion": "reservas_por_clase", "id_clase": id_clase})
    if resp_reser is None:
        return {"ok": False, "error": "Servicio 'reser' no disponible"}
    if not resp_reser.get("ok"):
        return {"ok": False, "error": resp_reser.get("error", "Error consultando reservas")}

    reservas = resp_reser.get("reservas", [])
    ruts = [r.get("rut_alumno") or r.get("rut") for r in reservas]
    ruts = [r for r in ruts if r]

    nombres = {}
    resp_usrol = llamar_servicio("usrol", {"accion": "listar"})
    if resp_usrol is not None and resp_usrol.get("ok"):
        for u in resp_usrol.get("usuarios", []):
            if u.get("rut"):
                nombres[u["rut"]] = u.get("nombre", "")

    alumnos = [{"rut": rut, "nombre": nombres.get(rut, "")} for rut in ruts]
    return {"ok": True, "alumnos": alumnos}

def accion_clases_profe(datos):
    rut_profe = datos.get("rut_profe")
    if not rut_profe:
        return {"ok": False, "error": "Falta parametro: rut_profe"}
    fecha = datos.get("fecha")

    peticion = {"accion": "listar_clases"}
    if fecha:
        peticion["fecha"] = fecha
    resp_clase = llamar_servicio("clase", peticion)
    if resp_clase is None:
        return {"ok": False, "error": "Servicio 'clase' no disponible"}
    if not resp_clase.get("ok"):
        return {"ok": False, "error": resp_clase.get("error", "Error consultando clases")}

    clases = resp_clase.get("clases", [])
    agenda = [
        c for c in clases
        if (c.get("rut_profe") == rut_profe or c.get("profe") == rut_profe)
        and (not fecha or c.get("fecha") == fecha)
    ]
    return {"ok": True, "clases": agenda}

def procesar(datos_json):
    try:
        datos = json.loads(datos_json)
    except json.JSONDecodeError:
        return json.dumps({"ok": False, "error": "JSON invalido"})

    accion = datos.get("accion")
    if accion == "crear_profe":
        return json.dumps(accion_crear_profe(datos))
    if accion == "listar_profes":
        return json.dumps(accion_listar_profes())
    if accion == "asistencia":
        return json.dumps(accion_asistencia(datos))
    if accion == "clases_profe":
        return json.dumps(accion_clases_profe(datos))
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
        payload = data[5:].decode()
        print(f"Peticion recibida: {payload}")
        respuesta = procesar(payload)
        send_message(sock, NOMBRE_SERVICIO, respuesta)
        print(f"Respuesta enviada: {respuesta}")
except Exception as e:
    print(f"Error: {e}")
finally:
    sock.close()