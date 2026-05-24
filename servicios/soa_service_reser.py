from soa_lib import connect_to_bus, send_message, receive_message
import json
import os
import uuid
from datetime import datetime

NOMBRE_SERVICIO = "reser"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCHIVO_RESERVAS = os.path.join(BASE_DIR, "data", "reservas.json")

def cargar_reservas():
    if not os.path.exists(ARCHIVO_RESERVAS):
        return []
    with open(ARCHIVO_RESERVAS, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_reservas(reservas):
    os.makedirs(os.path.dirname(ARCHIVO_RESERVAS), exist_ok=True)
    with open(ARCHIVO_RESERVAS, "w", encoding="utf-8") as f:
        json.dump(reservas, f, indent=2, ensure_ascii=False)

def llamar_servicio(nombre_servicio, accion, params):
    sock_interno = None
    try:
        sock_interno = connect_to_bus()
        payload = json.dumps({"accion": accion, **params})
        send_message(sock_interno, nombre_servicio, payload)
        data = receive_message(sock_interno)
        if not data:
            return {"ok": False, "error": f"Sin respuesta del servicio '{nombre_servicio}'"}
        contenido = data[5:].decode()
        if contenido.startswith("OK"):
            return json.loads(contenido[2:])
        else:
            return {"ok": False, "error": f"Bus rechazó la solicitud a '{nombre_servicio}'"}
    except Exception as e:
        return {"ok": False, "error": f"Error llamando a '{nombre_servicio}': {str(e)}"}
    finally:
        if sock_interno:
            sock_interno.close()

def reservar(datos):
    if "rut_alumno" not in datos or "id_clase" not in datos:
        return {"ok": False, "error": "Faltan campos 'rut_alumno' o 'id_clase'"}

    rut = datos["rut_alumno"]
    id_clase = datos["id_clase"]

    print(f"  [reser] Verificando clase {id_clase}...")
    resp_clase = llamar_servicio("clase", "obtener_clase", {"id_clase": id_clase})
    if not resp_clase.get("ok"):
        return {"ok": False, "error": resp_clase.get("error", "Clase no encontrada")}

    clase = resp_clase["clase"]
    if clase["cupos_disponibles"] <= 0:
        return {"ok": False, "error": "Sin cupos disponibles en esta clase"}

    reservas = cargar_reservas()
    for r in reservas:
        if r["rut_alumno"] == rut and r["id_clase"] == id_clase and r["estado"] == "activa":
            return {"ok": False, "error": "El alumno ya tiene una reserva activa en esta clase"}

    print(f"  [reser] Verificando plan del alumno {rut}...")
    resp_plan = llamar_servicio("plans", "verificar", {"rut_alumno": rut})
    if not resp_plan.get("ok"):
        return {"ok": False, "error": resp_plan.get("error", "Error al verificar plan")}

    if not resp_plan.get("vigente"):
        return {"ok": False, "error": "El plan del alumno está vencido o inactivo"}
    if resp_plan.get("clases_restantes", 0) <= 0:
        return {"ok": False, "error": "El alumno no tiene clases disponibles en su plan"}

    print(f"  [reser] Descontando clase del plan de {rut}...")
    resp_descuento = llamar_servicio("plans", "descontar", {"rut_alumno": rut})
    if not resp_descuento.get("ok"):
        return {"ok": False, "error": resp_descuento.get("error", "Error al descontar clase del plan")}

    print(f"  [reser] Actualizando cupo de clase {id_clase}...")
    resp_cupo = llamar_servicio("clase", "actualizar_cupo", {
        "id_clase": id_clase,
        "delta": -1,
        "rut_alumno": rut
    })
    if not resp_cupo.get("ok"):
        llamar_servicio("plans", "devolver", {"rut_alumno": rut})
        return {"ok": False, "error": resp_cupo.get("error", "Error al actualizar cupo")}

    nueva_reserva = {
        "id_reserva": str(uuid.uuid4())[:8],
        "rut_alumno": rut,
        "id_clase": id_clase,
        "fecha_reserva": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "estado": "activa"
    }
    reservas.append(nueva_reserva)
    guardar_reservas(reservas)

    print(f"  → Reserva creada: {nueva_reserva['id_reserva']} | alumno={rut} | clase={id_clase}")
    return {"ok": True, "id_reserva": nueva_reserva["id_reserva"]}


def cancelar(datos):
    if "id_reserva" not in datos:
        return {"ok": False, "error": "Falta el campo 'id_reserva'"}

    reservas = cargar_reservas()
    for r in reservas:
        if r["id_reserva"] == datos["id_reserva"]:
            if r["estado"] != "activa":
                return {"ok": False, "error": "La reserva ya fue cancelada"}

            rut = r["rut_alumno"]
            id_clase = r["id_clase"]

            print(f"  [reser] Devolviendo clase al plan de {rut}...")
            llamar_servicio("plans", "devolver", {"rut_alumno": rut})

            print(f"  [reser] Liberando cupo en clase {id_clase}...")
            llamar_servicio("clase", "actualizar_cupo", {
                "id_clase": id_clase,
                "delta": 1,
                "rut_alumno": rut
            })

            r["estado"] = "cancelada"
            r["fecha_cancelacion"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            guardar_reservas(reservas)

            print(f"  → Reserva {datos['id_reserva']} cancelada.")
            return {"ok": True}

    return {"ok": False, "error": f"Reserva '{datos['id_reserva']}' no encontrada"}


def listar_reservas(datos):
    if "rut_alumno" not in datos:
        return {"ok": False, "error": "Falta el campo 'rut_alumno'"}

    reservas = cargar_reservas()
    mis_reservas = [r for r in reservas if r["rut_alumno"] == datos["rut_alumno"]]
    return {"ok": True, "reservas": mis_reservas}

ACCIONES = {
    "reservar":       reservar,
    "cancelar":       cancelar,
    "listar_reservas": listar_reservas,
}

def procesar(payload_str):
    try:
        datos = json.loads(payload_str)
    except json.JSONDecodeError:
        return json.dumps({"ok": False, "error": "JSON inválido"})

    accion = datos.get("accion")
    if not accion:
        return json.dumps({"ok": False, "error": "Falta el campo 'accion'"})

    handler = ACCIONES.get(accion)
    if not handler:
        return json.dumps({"ok": False, "error": f"Acción desconocida: '{accion}'"})

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
    print(f"Confirmación del bus: {init_data!r}")
    print(f"Servicio '{NOMBRE_SERVICIO}' listo.\n")

    while True:
        data = receive_message(sock)
        if not data:
            print("Conexión cerrada por el bus.")
            break

        payload = data[5:].decode()
        print(f"[reser] Solicitud recibida: {payload}")

        respuesta = procesar(payload)
        send_message(sock, NOMBRE_SERVICIO, respuesta)
        print(f"[reser] Respuesta enviada: {respuesta}\n")

except Exception as e:
    print(f"Error en el servicio: {e}")
finally:
    print("Cerrando socket del servicio 'reser'")
    sock.close()