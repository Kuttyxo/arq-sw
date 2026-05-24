import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from soa_lib import connect_to_bus, send_message, receive_message
import json

NOMBRE_SERVICIO = "usrol"
ARCHIVO_USUARIOS = "data/usuarios.json"

def cargar_usuarios():
    if not os.path.exists(ARCHIVO_USUARIOS):
        return {}
    with open(ARCHIVO_USUARIOS, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_usuarios(usuarios):
    with open(ARCHIVO_USUARIOS, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, indent=4, ensure_ascii=False)

def procesar(datos_json):
    try:
        solicitud = json.loads(datos_json)
        accion = solicitud.get("accion")
        usuarios = cargar_usuarios()

        if accion == "login":
            rut = solicitud.get("rut")
            password = solicitud.get("password")
            usuario = usuarios.get(rut)
            if usuario and usuario["password"] == password:
                return json.dumps({"ok": True, "rol": usuario["rol"], "nombre": usuario["nombre"]})
            else:
                return json.dumps({"ok": False, "error": "RUT o contrasena incorrectos"})

        elif accion == "crear":
            rut = solicitud.get("rut")
            if rut in usuarios:
                return json.dumps({"ok": False, "error": "RUT ya existe"})
            usuarios[rut] = {
                "rut": rut,
                "nombre": solicitud.get("nombre"),
                "email": solicitud.get("email"),
                "password": solicitud.get("password"),
                "rol": solicitud.get("rol"),
                "plan_activo": None,
                "clases_restantes": 0,
                "fecha_vencimiento": None
            }
            guardar_usuarios(usuarios)
            return json.dumps({"ok": True, "mensaje": "Usuario creado"})

        elif accion == "listar_usuarios" or accion == "listar":
            lista = []
            for rut, datos in usuarios.items():
                lista.append({
                    "rut": rut,
                    "nombre": datos["nombre"],
                    "email": datos["email"],
                    "rol": datos["rol"]
                })
            return json.dumps({"ok": True, "usuarios": lista})

        elif accion == "buscar_usuario" or accion == "obtener":
            rut = solicitud.get("rut")
            if rut not in usuarios:
                return json.dumps({"ok": False, "error": "Usuario no existe"})
            copia = usuarios[rut].copy()
            del copia["password"]
            return json.dumps({"ok": True, "usuario": copia})

        else:
            return json.dumps({"ok": False, "error": f"Accion '{accion}' no soportada"})

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
        # Saltar 10 bytes: 5 del largo + 5 del nombre del servicio
        payload = data[10:].decode()
        respuesta = procesar(payload)
        send_message(sock, NOMBRE_SERVICIO, respuesta)
except Exception as e:
    print(f"Error: {e}")
finally:
    sock.close()