import os
import sys

# soa_lib.py vive en la raiz del repo; los clientes estan en clientes/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from soa_lib import connect_to_bus, send_message, receive_message
import json
from datetime import date, datetime, timedelta

NOMBRE_SERVICIO = "profe"


def consultar(sock, peticion):
    send_message(sock, NOMBRE_SERVICIO, json.dumps(peticion))
    data = receive_message(sock)
    if not data:
        return None
    # El BUS responde <5-servicio><OK><payload>; se quitan ambos prefijos.
    cuerpo = data[5:].decode()
    if cuerpo[:2] == "OK":
        cuerpo = cuerpo[2:]
    try:
        return json.loads(cuerpo)
    except json.JSONDecodeError:
        return None


def imprimir_clases(clases):
    if not clases:
        print("  (sin clases)")
        return
    for c in clases:
        idc = c.get("id_clase") or c.get("id", "?")
        disc = c.get("disciplina", "?")
        fecha = c.get("fecha", "?")
        hora = c.get("hora", "?")
        print(f"  - [{idc}] {disc} | {fecha} {hora}")


def ver_clases_hoy(sock, rut_profe):
    hoy = date.today().isoformat()
    resp = consultar(sock, {"accion": "clases_profe", "rut_profe": rut_profe, "fecha": hoy})
    if resp is None:
        print("Sin respuesta del servicio.")
        return
    if not resp.get("ok"):
        print(f"Error: {resp.get('error')}")
        return
    print(f"\nClases de hoy ({hoy}):")
    imprimir_clases(resp.get("clases", []))


def ver_alumnos_clase(sock):
    id_clase = input("Ingrese id de la clase: ").strip()
    resp = consultar(sock, {"accion": "asistencia", "id_clase": id_clase})
    if resp is None:
        print("Sin respuesta del servicio.")
        return
    if not resp.get("ok"):
        print(f"Error: {resp.get('error')}")
        return
    alumnos = resp.get("alumnos", [])
    print(f"\nAlumnos inscritos en la clase {id_clase}:")
    if not alumnos:
        print("  (sin alumnos)")
    for a in alumnos:
        print(f"  - {a.get('rut')} | {a.get('nombre')}")


def ver_clases_semana(sock, rut_profe):
    resp = consultar(sock, {"accion": "clases_profe", "rut_profe": rut_profe})
    if resp is None:
        print("Sin respuesta del servicio.")
        return
    if not resp.get("ok"):
        print(f"Error: {resp.get('error')}")
        return
    hoy = date.today()
    fin = hoy + timedelta(days=6)
    semana = []
    for c in resp.get("clases", []):
        try:
            f = datetime.strptime(c.get("fecha", ""), "%Y-%m-%d").date()
        except ValueError:
            continue
        if hoy <= f <= fin:
            semana.append(c)
    print(f"\nClases de la semana ({hoy.isoformat()} a {fin.isoformat()}):")
    imprimir_clases(semana)


sock = connect_to_bus()
try:
    rut_profe = input("Ingrese su RUT de profesor: ").strip()
    while True:
        print("\n--- Coliseo OS | Profesor ---")
        print("1. Ver mis clases de hoy")
        print("2. Ver lista de alumnos de una clase")
        print("3. Ver mis clases de la semana")
        print("9. Salir")
        opcion = input("Opcion: ").strip()

        if opcion == "1":
            ver_clases_hoy(sock, rut_profe)
        elif opcion == "2":
            ver_alumnos_clase(sock)
        elif opcion == "3":
            ver_clases_semana(sock, rut_profe)
        elif opcion == "9":
            break
        else:
            print("Opcion invalida.")
finally:
    sock.close()
