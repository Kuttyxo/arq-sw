import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from soa_lib import connect_to_bus, send_message, receive_message
import json

def enviar_solicitud(nombre_servicio, accion, parametros):
    sock = connect_to_bus()
    try:
        payload_dict = {"accion": accion}
        payload_dict.update(parametros)
        payload = json.dumps(payload_dict)
        send_message(sock, nombre_servicio, payload)
        data = receive_message(sock)
        if not data:
            return {"ok": False, "error": "Sin respuesta"}
        data_str = data.decode()
        json_start = data_str.index("{")
        respuesta = json.loads(data_str[json_start:])
        return respuesta
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        sock.close()

def menu_gestionar_usuarios():
    while True:
        print("\n--- Gestionar Usuarios ---")
        print("1. Ver todos los alumnos")
        print("2. Buscar alumno por RUT")
        print("3. Volver")
        op = str(input("\nOpcion: "))

        if op == "1":
            respuesta = enviar_solicitud("usrol", "listar_usuarios", {})
            if respuesta.get("ok"):
                usuarios = respuesta.get("usuarios", [])
                if not usuarios:
                    print("Sin usuarios registrados")
                else:
                    for u in usuarios:
                        print(f"- {u.get('rut')} | {u.get('nombre')} | {u.get('rol')}")
            else:
                print(f"Error: {respuesta.get('error', '')}")

        elif op == "2":
            rut = str(input("RUT: "))
            respuesta = enviar_solicitud("usrol", "buscar_usuario", {"rut": rut})
            if respuesta.get("ok"):
                u = respuesta.get("usuario", {})
                print(f"Nombre: {u.get('nombre')}")
                print(f"Email:  {u.get('email')}")
                print(f"Rol:    {u.get('rol')}")
                print(f"Plan:   {u.get('plan_activo')}")
            else:
                print(f"Error: {respuesta.get('error', '')}")

        elif op == "3":
            break
        else:
            print("Opcion invalida")

def menu_gestionar_planes():
    while True:
        print("\n--- Gestionar Planes ---")
        print("1. Ver todos los planes")
        print("2. Modificar precio de un plan")
        print("3. Volver")
        op = str(input("\nOpcion: "))

        if op == "1":
            respuesta = enviar_solicitud("plans", "listar_planes", {})
            if respuesta.get("ok"):
                planes = respuesta.get("planes", [])
                if not planes:
                    print("Sin planes registrados")
                else:
                    for p in planes:
                        print(f"- {p.get('id')} | {p.get('nombre')} | ${p.get('precio')}")
            else:
                print(f"Error: {respuesta.get('error', '')}")

        elif op == "2":
            id_plan = str(input("ID del plan: "))
            try:
                precio_nuevo = int(input("Precio nuevo: "))
            except ValueError:
                print("Precio invalido")
                continue

            # obtener precio actual para registrar en auditoria
            resp_actual = enviar_solicitud("plans", "buscar_plan", {"id_plan": id_plan})
            precio_anterior = "desconocido"
            if resp_actual.get("ok"):
                precio_anterior = str(resp_actual.get("plan", {}).get("precio", "desconocido"))

            # modificar precio en plans
            respuesta = enviar_solicitud("plans", "modificar_precio", {
                "id_plan": id_plan,
                "precio_nuevo": precio_nuevo
            })
            if respuesta.get("ok"):
                print("Precio actualizado")
                # registrar el cambio en auditoria
                enviar_solicitud("audit", "registrar_cambio", {
                    "quien": "admin",
                    "que_cambio": "precio_plan",
                    "valor_anterior": precio_anterior,
                    "valor_nuevo": str(precio_nuevo),
                    "entidad": id_plan
                })
                print("Cambio registrado en auditoria")
            else:
                print(f"Error: {respuesta.get('error', '')}")

        elif op == "3":
            break
        else:
            print("Opcion invalida")

def menu_registrar_pago():
    print("\n--- Registrar Pago en Efectivo ---")
    rut = str(input("RUT alumno: "))
    id_plan = str(input("ID plan: "))
    try:
        monto = int(input("Monto: "))
    except ValueError:
        print("Monto invalido")
        return

    respuesta = enviar_solicitud("pagos", "registrar_pago", {
        "rut_alumno": rut,
        "id_plan": id_plan,
        "monto": monto,
        "metodo": "efectivo"
    })

    if respuesta.get("ok"):
        id_pago = respuesta.get("id_pago")
        print(f"Pago registrado: {id_pago}")
        print(f"Estado: {respuesta.get('estado', '')}")
        print(f"Fecha:  {respuesta.get('fecha_pago', '')[:19]}")
        # registrar en auditoria
        enviar_solicitud("audit", "registrar_cambio", {
            "quien": "admin",
            "que_cambio": "pago_registrado",
            "valor_anterior": "sin_pago",
            "valor_nuevo": id_pago,
            "entidad": rut
        })
        print("Auditoria actualizada")
    else:
        print(f"Error: {respuesta.get('error', '')}")

def menu_ver_pagos():
    print("\n--- Ver Historial de Pagos ---")
    rut = str(input("RUT alumno: "))
    respuesta = enviar_solicitud("pagos", "listar_pagos", {"rut_alumno": rut})
    if respuesta.get("ok"):
        pagos = respuesta.get("pagos", [])
        if not pagos:
            print("Sin pagos registrados")
        else:
            for p in pagos:
                print(f"- {p.get('id_pago')} | ${p.get('monto')} | {p.get('estado')}")
            # ver comprobante desde el historial de pagos
            id_comp = str(input("\nID para ver comprobante (Enter para volver): "))
            if id_comp:
                resp_comp = enviar_solicitud("pagos", "comprobante", {"id_pago": id_comp})
                if resp_comp.get("ok"):
                    print(resp_comp.get("texto", ""))
                else:
                    print(f"Error: {resp_comp.get('error', '')}")
    else:
        print(f"Error: {respuesta.get('error', '')}")

def menu_ver_auditoria():
    print("\n--- Historial de Cambios (Auditoria) ---")
    fecha = str(input("Fecha desde (AAAA-MM-DD, Enter para todos): "))
    params = {}
    if fecha:
        params["fecha_desde"] = fecha
    respuesta = enviar_solicitud("audit", "listar_historial", params)
    if respuesta.get("ok"):
        registros = respuesta.get("historial", [])
        print(f"Total: {respuesta.get('total', 0)}")
        if not registros:
            print("Sin registros")
        else:
            for r in registros:
                print(f"- [{r.get('fecha', '')[:19]}] {r.get('quien')} | {r.get('accion')} | {r.get('entidad')} | {r.get('valor_anterior')} -> {r.get('valor_nuevo')}")
    else:
        print(f"Error: {respuesta.get('error', '')}")

def main():
    print("--- Coliseo OS | Administrador ---")
    while True:
        print("\n1. Gestionar usuarios")
        print("2. Gestionar planes")
        print("3. Registrar pago en efectivo")
        print("4. Ver historial de pagos")
        print("5. Ver historial de cambios (auditoria)")
        print("9. Salir")
        opcion = str(input("\nOpcion: "))
        if opcion == "1":
            menu_gestionar_usuarios()
        elif opcion == "2":
            menu_gestionar_planes()
        elif opcion == "3":
            menu_registrar_pago()
        elif opcion == "4":
            menu_ver_pagos()
        elif opcion == "5":
            menu_ver_auditoria()
        elif opcion == "9":
            print("Saliendo...")
            break
        else:
            print("Opcion invalida")

if __name__ == "__main__":
    main()
