import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from soa_lib import connect_to_bus, send_message, receive_message
import json
from datetime import datetime

NOMBRE_SERVICIO = "pagos"
DATA_DIR = "data"
PAGOS_FILE = os.path.join(DATA_DIR, "pagos.json")

def cargar_pagos():
    if os.path.exists(PAGOS_FILE):
        with open(PAGOS_FILE, 'r') as f:
            return json.load(f)
    return []

def guardar_pagos(pagos):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(PAGOS_FILE, 'w') as f:
        json.dump(pagos, f, indent=2)

def cargar_usuarios():
    ruta = os.path.join(DATA_DIR, "usuarios.json")
    if os.path.exists(ruta):
        with open(ruta, 'r') as f:
            return json.load(f)
    return {}

def cargar_planes():
    ruta = os.path.join(DATA_DIR, "planes.json")
    if os.path.exists(ruta):
        with open(ruta, 'r') as f:
            return json.load(f)
    return {}

def usuario_existe(rut):
    usuarios = cargar_usuarios()
    return rut in usuarios

def obtener_plan(id_plan):
    planes = cargar_planes()
    return planes.get(id_plan)

def llamar_plans(rut_alumno, id_plan, duracion_meses):
    sock2 = None
    try:
        sock2 = connect_to_bus()
        sock2.settimeout(5)
        payload = json.dumps({
            "accion": "activar_plan",
            "rut_alumno": rut_alumno,
            "id_plan": id_plan,
            "duracion_meses": duracion_meses
        })
        send_message(sock2, "plans", payload)
        data = receive_message(sock2)
        if not data:
            return False, "Sin respuesta de plans"
        cuerpo = data[5:].decode()
        # El BUS responde <5-servicio><OK><payload>; se quita el prefijo OK.
        if cuerpo[:2] == "OK":
            cuerpo = cuerpo[2:]
        resp = json.loads(cuerpo)
        if resp.get("ok"):
            return True, None
        return False, resp.get("error", "Error en plans")
    except Exception as e:
        return False, f"plans no disponible: {e}"
    finally:
        if sock2:
            sock2.close()

def registrar_pago(datos):
    rut_alumno = datos.get("rut_alumno")
    id_plan = datos.get("id_plan")
    monto = datos.get("monto")
    metodo = datos.get("metodo")

    if not rut_alumno or not id_plan or not metodo or monto is None:
        return json.dumps({"ok": False, "error": "Faltan parametros"})

    if not usuario_existe(rut_alumno):
        return json.dumps({"ok": False, "error": "Usuario no existe"})

    plan = obtener_plan(id_plan)
    if not plan:
        return json.dumps({"ok": False, "error": "Plan no existe"})

    pagos = cargar_pagos()
    ahora = datetime.now()
    id_pago = "pago_" + ahora.strftime('%Y%m%d_%H%M%S')

    nuevo_pago = {
        "id_pago": id_pago,
        "rut_alumno": rut_alumno,
        "id_plan": id_plan,
        "monto": monto,
        "metodo": metodo,
        "estado": "aprobado",
        "fecha_pago": ahora.isoformat(),
        "codigo_transaccion": "TXN" + ahora.strftime('%Y%m%d%H%M%S')
    }
    pagos.append(nuevo_pago)
    guardar_pagos(pagos)
    print(f"[pagos] Pago guardado: {id_pago}")

    ok_plans, err_plans = llamar_plans(rut_alumno, id_plan, plan.get("duracion_meses", 1))
    if not ok_plans:
        pagos_actuales = cargar_pagos()
        pagos_sin_rollback = []
        for p in pagos_actuales:
            if p.get("id_pago") != id_pago:
                pagos_sin_rollback.append(p)
        guardar_pagos(pagos_sin_rollback)
        print(f"[pagos] ROLLBACK ejecutado - plans fallo: {err_plans}")
        return json.dumps({"ok": False, "error": f"Fallo activacion de plan: {err_plans}"})

    print("[pagos] Plan activado correctamente")
    return json.dumps({
        "ok": True,
        "id_pago": id_pago,
        "estado": "aprobado",
        "fecha_pago": nuevo_pago["fecha_pago"]
    })

def listar_pagos(datos):
    rut_alumno = datos.get("rut_alumno")
    if not rut_alumno:
        return json.dumps({"ok": False, "error": "Falta rut_alumno"})

    pagos = cargar_pagos()
    pagos_usuario = []
    for p in pagos:
        if p.get("rut_alumno") == rut_alumno:
            pagos_usuario.append({
                "id_pago": p.get("id_pago"),
                "fecha": p.get("fecha_pago"),
                "monto": p.get("monto"),
                "plan": p.get("id_plan"),
                "metodo": p.get("metodo"),
                "estado": p.get("estado")
            })
    return json.dumps({"ok": True, "pagos": pagos_usuario})

def obtener_comprobante(datos):
    id_pago = datos.get("id_pago")
    if not id_pago:
        return json.dumps({"ok": False, "error": "Falta id_pago"})

    pagos = cargar_pagos()
    pago = None
    for p in pagos:
        if p.get("id_pago") == id_pago:
            pago = p
            break

    if not pago:
        return json.dumps({"ok": False, "error": "Pago no encontrado"})

    comprobante = (
        "================================\n"
        "   COMPROBANTE DE PAGO\n"
        "   COLISEO CLUB RESORT - MAIPU\n"
        "================================\n"
        f"ID:      {pago.get('id_pago')}\n"
        f"RUT:     {pago.get('rut_alumno')}\n"
        f"Plan:    {pago.get('id_plan')}\n"
        f"Monto:   ${pago.get('monto')}\n"
        f"Metodo:  {pago.get('metodo')}\n"
        f"Estado:  {pago.get('estado')}\n"
        f"Fecha:   {pago.get('fecha_pago')[:19]}\n"
        f"Codigo:  {pago.get('codigo_transaccion')}\n"
        "================================"
    )
    return json.dumps({"ok": True, "texto": comprobante})

def procesar(payload_str):
    try:
        datos = json.loads(payload_str)
        accion = datos.get("accion")
        if accion == "registrar_pago":
            return registrar_pago(datos)
        elif accion == "listar_pagos":
            return listar_pagos(datos)
        elif accion == "comprobante":
            return obtener_comprobante(datos)
        else:
            return json.dumps({"ok": False, "error": "Accion desconocida"})
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)})

def main():
    sock = connect_to_bus()
    try:
        send_message(sock, "sinit", NOMBRE_SERVICIO)
        init_data = receive_message(sock)
        print(f"Servicio {NOMBRE_SERVICIO} registrado")
        print("[pagos] Esperando solicitudes...")
        while True:
            data = receive_message(sock)
            if not data:
                break
            payload = data[5:].decode()
            print(f"[pagos] Solicitud recibida: {payload[:60]}")
            respuesta = procesar(payload)
            send_message(sock, NOMBRE_SERVICIO, respuesta)
            print("[pagos] Respuesta enviada")
    except KeyboardInterrupt:
        print("[pagos] Detenido")
    except Exception as e:
        print(f"[pagos] Error: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    main()
