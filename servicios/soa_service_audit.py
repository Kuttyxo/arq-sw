import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from soa_lib import connect_to_bus, send_message, receive_message
import json
from datetime import datetime

NOMBRE_SERVICIO = "audit"
DATA_DIR = "data"
HISTORIAL_FILE = os.path.join(DATA_DIR, "historial.json")

def cargar_historial():
    if os.path.exists(HISTORIAL_FILE):
        with open(HISTORIAL_FILE, 'r') as f:
            return json.load(f)
    return []

def guardar_historial(historial):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(HISTORIAL_FILE, 'w') as f:
        json.dump(historial, f, indent=2)

def registrar_cambio(datos):
    quien = datos.get("quien")
    que_cambio = datos.get("que_cambio")
    valor_anterior = datos.get("valor_anterior")
    valor_nuevo = datos.get("valor_nuevo")
    entidad = datos.get("entidad", "N/A")

    if not quien or not que_cambio or valor_anterior is None or valor_nuevo is None:
        return {"ok": False, "error": "Faltan parametros"}

    historial = cargar_historial()
    ahora = datetime.now()
    id_evento = "evt_" + ahora.strftime('%Y%m%d_%H%M%S')

    evento = {
        "id_evento": id_evento,
        "quien": quien,
        "accion": que_cambio,
        "entidad": entidad,
        "valor_anterior": str(valor_anterior),
        "valor_nuevo": str(valor_nuevo),
        "fecha": ahora.isoformat()
    }
    historial.append(evento)
    guardar_historial(historial)
    print(f"[audit] Evento registrado: {id_evento}")
    return {"ok": True, "id_evento": id_evento}

def listar_historial(datos):
    fecha_desde = datos.get("fecha_desde")
    tipo = datos.get("tipo")

    historial = cargar_historial()

    if fecha_desde:
        filtrado = []
        for h in historial:
            if h.get("fecha", "").startswith(fecha_desde):
                filtrado.append(h)
        historial = filtrado

    if tipo:
        filtrado = []
        for h in historial:
            if h.get("accion") == tipo:
                filtrado.append(h)
        historial = filtrado

    historial = sorted(historial, key=lambda x: x.get("fecha", ""), reverse=True)
    return {"ok": True, "total": len(historial), "historial": historial}

def procesar(payload_str):
    try:
        datos = json.loads(payload_str)
        accion = datos.get("accion")
        if accion == "registrar_cambio":
            return json.dumps(registrar_cambio(datos))
        elif accion == "listar_historial":
            return json.dumps(listar_historial(datos))
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
        print("[audit] Esperando solicitudes...")
        while True:
            data = receive_message(sock)
            if not data:
                break
            payload = data[5:].decode()
            print("[audit] Solicitud recibida")
            respuesta = procesar(payload)
            send_message(sock, NOMBRE_SERVICIO, respuesta)
            print("[audit] Respuesta enviada")
    except KeyboardInterrupt:
        print("[audit] Detenido")
    except Exception as e:
        print(f"[audit] Error: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    main()