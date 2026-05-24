from soa_lib import connect_to_bus, send_message, receive_message
import json

def llamar_servicio(sock, nombre_servicio, accion, params=None):
    if params is None:
        params = {}
    payload = json.dumps({"accion": accion, **params})
    send_message(sock, nombre_servicio, payload)
    data = receive_message(sock)
    if not data:
        return {"ok": False, "error": "Sin respuesta del bus"}
    contenido = data[5:].decode()
    if contenido.startswith("OK"):
        return json.loads(contenido[2:])
    else:
        return {"ok": False, "error": "El bus reportó un error (NK)"}

def limpiar():
    print("\n" + "─" * 50)

def encabezado(titulo):
    limpiar()
    print(f"  COLISEO OS | {titulo}")
    print("─" * 50)

def ver_clases_disponibles(sock):
    encabezado("Clases Disponibles")
    fecha = input("  Filtrar por fecha (YYYY-MM-DD) o Enter para todas: ").strip()

    params = {}
    if fecha:
        params["fecha"] = fecha

    resp = llamar_servicio(sock, "clase", "listar_clases", params)
    if not resp.get("ok"):
        print(f"\n Error: {resp.get('error')}")
        return

    clases = resp.get("clases", [])
    if not clases:
        print("\n Sin clases disponibles para esa fecha.")
        return

    print(f"\n  {'ID':<10} {'Disciplina':<14} {'Fecha':<12} {'Hora':<6} {'Cupos':<8} {'Profe'}")
    print("  " + "─" * 60)
    for c in clases:
        cupos_str = f"{c['cupos_disponibles']}/{c['cupos_max']}"
        print(f"  {c['id_clase']:<10} {c['disciplina']:<14} {c['fecha']:<12} {c['hora']:<6} {cupos_str:<8} {c['rut_profe']}")


def reservar_clase(sock, rut_alumno):
    encabezado("Reservar clase")

    # Mostrar clases disponibles primero
    resp = llamar_servicio(sock, "clase", "listar_clases", {})
    if resp.get("ok") and resp.get("clases"):
        clases = [c for c in resp["clases"] if c["cupos_disponibles"] > 0]
        if not clases:
            print("\n  Sin clases con cupos disponibles.")
            return
        print(f"\n  {'ID':<10} {'Disciplina':<14} {'Fecha':<12} {'Hora':<6} {'Cupos'}")
        print("  " + "─" * 55)
        for c in clases:
            cupos_str = f"{c['cupos_disponibles']}/{c['cupos_max']}"
            print(f"  {c['id_clase']:<10} {c['disciplina']:<14} {c['fecha']:<12} {c['hora']:<6} {cupos_str}")

    id_clase = input("\n  Ingrese ID de la clase a reservar: ").strip()
    if not id_clase:
        print("  Operación cancelada.")
        return

    print(f"\n Procesando reserva")
    resp = llamar_servicio(sock, "reser", "reservar", {
        "rut_alumno": rut_alumno,
        "id_clase": id_clase
    })

    if resp.get("ok"):
        print(f"\n  Reserva confirmada. ID: {resp['id_reserva']}")
    else:
        print(f"\n  No se pudo reservar: {resp.get('error')}")


def ver_mis_reservas(sock, rut_alumno):
    encabezado("Mis Reservas")
    resp = llamar_servicio(sock, "reser", "listar_reservas", {"rut_alumno": rut_alumno})

    if not resp.get("ok"):
        print(f"\n  Error: {resp.get('error')}")
        return

    reservas = resp.get("reservas", [])
    activas = [r for r in reservas if r["estado"] == "activa"]
    canceladas = [r for r in reservas if r["estado"] == "cancelada"]

    if not reservas:
        print("\n  No tienes reservas registradas.")
        return

    if activas:
        print(f"\n  Reservas activas ({len(activas)})")
        print(f"  {'ID Reserva':<12} {'ID Clase':<10} {'Fecha Reserva'}")
        print("  " + "─" * 45)
        for r in activas:
            print(f"  {r['id_reserva']:<12} {r['id_clase']:<10} {r['fecha_reserva']}")

    if canceladas:
        print(f"\n  Reservas canceladas ({len(canceladas)})")
        print(f"  {'ID Reserva':<12} {'ID Clase':<10} {'Fecha Cancelacion'}")
        print("  " + "─" * 45)
        for r in canceladas:
            print(f"  {r['id_reserva']:<12} {r['id_clase']:<10} {r.get('fecha_cancelacion', '—')}")


def cancelar_reserva(sock, rut_alumno):
    encabezado("Cancelar Reserva")

    resp = llamar_servicio(sock, "reser", "listar_reservas", {"rut_alumno": rut_alumno})
    if resp.get("ok"):
        activas = [r for r in resp.get("reservas", []) if r["estado"] == "activa"]
        if not activas:
            print("\n  No tienes reservas activas")
            return
        print(f"\n  {'ID reserva':<12} {'ID clase':<10} {'Fecha reserva'}")
        print("  " + "─" * 45)
        for r in activas:
            print(f"  {r['id_reserva']:<12} {r['id_clase']:<10} {r['fecha_reserva']}")

    id_reserva = input("\n  Ingrese ID de la reserva a cancelar: ").strip()
    if not id_reserva:
        print("  Operacion cancelada.")
        return

    confirmar = input(f"  ¿Confirmar cancelacion de reserva {id_reserva}? (s/n): ").strip().lower()
    if confirmar != "s":
        print("  Cancelacion abortada.")
        return

    resp = llamar_servicio(sock, "reser", "cancelar", {"id_reserva": id_reserva})
    if resp.get("ok"):
        print(f"\n  Reserva {id_reserva} cancelada. Cupo liberado.")
    else:
        print(f"\n  Error: {resp.get('error')}")


def ver_mi_plan(sock, rut_alumno):
    encabezado("Mi Plan Activo")
    resp = llamar_servicio(sock, "plans", "verificar", {"rut_alumno": rut_alumno})

    if not resp.get("ok"):
        print(f"\n  Error: {resp.get('error')}")
        return

    vigente = resp.get("vigente", False)
    clases = resp.get("clases_restantes", 0)
    vencimiento = resp.get("fecha_vencimiento", "—")

    estado = "Vigente" if vigente else "Vencido"
    print(f"\n  Estado del plan:    {estado}")
    print(f"  Clases restantes:   {clases}")
    print(f"  Fecha vencimiento:  {vencimiento}")


def login(sock):
    encabezado("Iniciar Sesión")
    rut = input("  RUT: ").strip()
    password = input("  Contraseña: ").strip()

    resp = llamar_servicio(sock, "usrol", "login", {"rut": rut, "password": password})
    if not resp.get("ok"):
        print(f"\n  {resp.get('error', 'Credenciales incorrectas')}")
        return None, None

    rol = resp.get("rol")
    if rol != "alumno":
        print(f"\n  Este cliente es solo para alumnos. Tu rol es '{rol}'.")
        return None, None

    print(f"\n  Bienvenido, {rut}.")
    return rut, rol


def menu(sock, rut_alumno):
    while True:
        encabezado("Menú Alumno")
        print(f"  Usuario: {rut_alumno}\n")
        print("  1. Ver clases disponibles")
        print("  2. Reservar clase")
        print("  3. Ver mis reservas")
        print("  4. Cancelar reserva")
        print("  5. Ver mi plan activo")
        print("  9. Salir")
        print()

        opcion = input("  Ingrese opción: ").strip()

        if opcion == "1":
            ver_clases_disponibles(sock)
        elif opcion == "2":
            reservar_clase(sock, rut_alumno)
        elif opcion == "3":
            ver_mis_reservas(sock, rut_alumno)
        elif opcion == "4":
            cancelar_reserva(sock, rut_alumno)
        elif opcion == "5":
            ver_mi_plan(sock, rut_alumno)
        elif opcion == "9":
            print("\n  Hasta pronto")
            break
        else:
            print("\n  Opción inválida.")

        input("\n  [Enter para continuar]")

sock=connect_to_bus()
try:
    rut, rol=login(sock)
    if rut:
        menu(sock, rut)
finally:
    print("Cerrando conexion")
    sock.close()
