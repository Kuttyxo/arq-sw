"""
Script de prueba local — Cristobal (servicios profe + notif).

Requisitos:
  1. El BUS del profesor corriendo en localhost:5000.
       docker run -d --name soabus -p 5000:5000 jrgiadach/soabus:v1
  2. Los servicios 'profe' y 'notif' levantados en otras terminales:
       python3 servicios/soa_service_profe.py
       python3 servicios/soa_service_notif.py

Uso:
  python3 prueba_local.py
"""
import json
from soa_lib import connect_to_bus, send_message, receive_message


def llamar(servicio, payload):
    sock = connect_to_bus()
    try:
        send_message(sock, servicio, json.dumps(payload))
        data = receive_message(sock)
        if not data:
            return None
        cuerpo = data[5:].decode()
        if cuerpo[:2] == "OK":
            cuerpo = cuerpo[2:]
        return json.loads(cuerpo)
    finally:
        sock.close()


def titulo(texto):
    print("\n" + "=" * 60)
    print(texto)
    print("=" * 60)


titulo("1) profe.crear_profe (alta de Ana)")
print(llamar("profe", {
    "accion": "crear_profe",
    "rut": "11.111.111-1",
    "nombre": "Ana Perez",
    "especialidad": "Boxeo",
}))

titulo("2) profe.crear_profe (mismo RUT -> debe rechazar)")
print(llamar("profe", {
    "accion": "crear_profe",
    "rut": "11.111.111-1",
    "nombre": "Ana Perez",
    "especialidad": "Boxeo",
}))

titulo("3) profe.crear_profe (sin nombre -> debe rechazar)")
print(llamar("profe", {
    "accion": "crear_profe",
    "rut": "22.222.222-2",
    "especialidad": "Yoga",
}))

titulo("4) profe.crear_profe (alta de Pedro)")
print(llamar("profe", {
    "accion": "crear_profe",
    "rut": "33.333.333-3",
    "nombre": "Pedro Soto",
    "especialidad": "Crossfit",
}))

titulo("5) profe.listar_profes")
print(llamar("profe", {"accion": "listar_profes"}))

titulo("6) profe.asistencia (fallara: depende del servicio 'reser' del equipo)")
print(llamar("profe", {"accion": "asistencia", "id_clase": "c1"}))

titulo("7) profe.accion_desconocida")
print(llamar("profe", {"accion": "no_existe"}))

titulo("8) notif.enviar")
print(llamar("notif", {
    "accion": "enviar",
    "rut_destino": "44.444.444-4",
    "tipo": "clase",
    "mensaje": "Tu clase de Box es hoy a las 18:00",
}))
print(llamar("notif", {
    "accion": "enviar",
    "rut_destino": "44.444.444-4",
    "tipo": "pago",
    "mensaje": "Pago recibido, gracias",
}))

titulo("9) notif.enviar (sin mensaje -> debe rechazar)")
print(llamar("notif", {
    "accion": "enviar",
    "rut_destino": "44.444.444-4",
    "tipo": "clase",
}))

titulo("10) notif.listar_pendientes")
print(llamar("notif", {"accion": "listar_pendientes", "rut_destino": "44.444.444-4"}))

titulo("11) notif.listar_pendientes (RUT sin notificaciones)")
print(llamar("notif", {"accion": "listar_pendientes", "rut_destino": "99.999.999-9"}))

print("\nListo. Revisa data/profesores.json y data/notificaciones.json para")
print("confirmar la persistencia.")
