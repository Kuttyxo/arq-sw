import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from soa_lib import connect_to_bus, send_message, receive_message
import json
from datetime import datetime, timedelta

NOMBRE_SERVICIO = "plans"
ARCHIVO_USUARIOS = "data/usuarios.json"
ARCHIVO_PLANES = "data/planes.json"

def cargar_usuarios():
    with open(ARCHIVO_USUARIOS, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_usuarios(usuarios):
    with open(ARCHIVO_USUARIOS, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, indent=4, ensure_ascii=False)

def cargar_planes():
    with open(ARCHIVO_PLANES, "r", encoding="utf-8") as f:
        return json.load(f)

def procesar(datos_json):
    try:
        solicitud = json.loads(datos_json)
        accion = solicitud.get("accion")
        usuarios = cargar_usuarios()
        planes = cargar_planes()

        if accion == "listar_planes":
            lista_planes = list(planes.values())
            return json.dumps({"ok": True, "planes": lista_planes})

        elif accion == "buscar_plan":
            id_plan = solicitud.get("id_plan")
            if id_plan not in planes:
                return json.dumps({"ok": False, "error": "Plan no existe"})
            return json.dumps({"ok": True, "plan": planes[id_plan]})

        elif accion == "modificar_precio":
            id_plan = solicitud.get("id_plan")
            precio_nuevo = solicitud.get("precio_nuevo")
            if id_plan not in planes:
                return json.dumps({"ok": False, "error": "Plan no existe"})
            planes[id_plan]["precio"] = precio_nuevo
            with open(ARCHIVO_PLANES, "w", encoding="utf-8") as f:
                json.dump(planes, f, indent=4, ensure_ascii=False)
            return json.dumps({"ok": True, "mensaje": "Precio actualizado"})

        elif accion == "asignar" or accion == "activar_plan":
            rut = solicitud.get("rut_alumno")
            id_plan = solicitud.get("id_plan")
            if rut not in usuarios:
                return json.dumps({"ok": False, "error": "Usuario no existe"})
            if id_plan not in planes:
                return json.dumps({"ok": False, "error": "Plan no existe"})
            plan = planes[id_plan]
            fecha_vencimiento = datetime.now() + timedelta(days=30 * plan["duracion_meses"])
            usuarios[rut]["plan_activo"] = id_plan
            usuarios[rut]["clases_restantes"] = plan["max_clases"]
            usuarios[rut]["fecha_vencimiento"] = fecha_vencimiento.strftime("%Y-%m-%d")
            guardar_usuarios(usuarios)
            return json.dumps({"ok": True, "fecha_vencimiento": usuarios[rut]["fecha_vencimiento"]})

        elif accion == "descontar":
            rut = solicitud.get("rut_alumno")
            if rut not in usuarios:
                return json.dumps({"ok": False, "error": "Usuario no existe"})
            usuario = usuarios[rut]
            if usuario["plan_activo"] is None:
                return json.dumps({"ok": False, "error": "Usuario sin plan activo"})
            hoy = datetime.now().date()
            fecha_venc = datetime.strptime(usuario["fecha_vencimiento"], "%Y-%m-%d").date()
            if fecha_venc < hoy:
                return json.dumps({"ok": False, "error": "Plan vencido"})
            if usuario["clases_restantes"] <= 0:
                return json.dumps({"ok": False, "error": "Sin clases restantes"})
            usuario["clases_restantes"] -= 1
            guardar_usuarios(usuarios)
            return json.dumps({"ok": True, "clases_restantes": usuario["clases_restantes"]})

        elif accion == "verificar":
            rut = solicitud.get("rut_alumno")
            if rut not in usuarios:
                return json.dumps({"ok": False, "error": "Usuario no existe"})
            usuario = usuarios[rut]
            vigente = False
            if usuario["plan_activo"]:
                hoy = datetime.now().date()
                fecha_venc = datetime.strptime(usuario["fecha_vencimiento"], "%Y-%m-%d").date()
                vigente = fecha_venc >= hoy
            return json.dumps({
                "ok": True,
                "clases_restantes": usuario["clases_restantes"],
                "vigente": vigente,
                "plan_activo": usuario["plan_activo"]
            })

        else:
            return json.dumps({"ok": False, "error": "Accion no soportada"})

    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)})

sock = connect_to_bus()
try:
    send_message(sock, "sinit", NOMBRE_SERVICIO)
    init_data = receive_message(sock)
    print(f"Servicio {NOMBRE_SERVICIO} registrado: {init_data!r}")
    while True:
        data = receive_message(sock)
        if not data:
            break
        payload = data[5:].decode()
        respuesta = procesar(payload)
        send_message(sock, NOMBRE_SERVICIO, respuesta)
except Exception as e:
    print(f"Error: {e}")
finally:
    sock.close()