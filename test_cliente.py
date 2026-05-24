from soa_lib import connect_to_bus, send_message, receive_message
import json

sock = connect_to_bus()

try:
    print("Probando servicio usrol - login")
    datos = json.dumps({"accion": "login", "rut": "12345678-9", "password": "1234"})
    send_message(sock, "usrol", datos)
    respuesta = receive_message(sock)
    respuesta_str = respuesta.decode()
    json_start = respuesta_str.find('{')
    respuesta_json = json.loads(respuesta_str[json_start:])
    print(f"Respuesta login: {respuesta_json}")

    print("\nProbando servicio plans - listar planes")
    datos2 = json.dumps({"accion": "listar_planes"})
    send_message(sock, "plans", datos2)
    respuesta2 = receive_message(sock)
    respuesta_str2 = respuesta2.decode()
    json_start2 = respuesta_str2.find('{')
    respuesta_json2 = json.loads(respuesta_str2[json_start2:])
    print(f"Respuesta listar planes: {respuesta_json2}")

    print("\nProbando servicio plans - verificar plan")
    datos3 = json.dumps({"accion": "verificar", "rut_alumno": "12345678-9"})
    send_message(sock, "plans", datos3)
    respuesta3 = receive_message(sock)
    respuesta_str3 = respuesta3.decode()
    json_start3 = respuesta_str3.find('{')
    respuesta_json3 = json.loads(respuesta_str3[json_start3:])
    print(f"Respuesta verificar plan: {respuesta_json3}")

    print("\nProbando servicio usrol - listar usuarios")
    datos4 = json.dumps({"accion": "listar"})
    send_message(sock, "usrol", datos4)
    respuesta4 = receive_message(sock)
    respuesta_str4 = respuesta4.decode()
    json_start4 = respuesta_str4.find('{')
    respuesta_json4 = json.loads(respuesta_str4[json_start4:])
    print(f"Respuesta listar usuarios: {respuesta_json4}")

    print("\nTodas las pruebas completadas con exito")

except Exception as e:
    print(f"Error: {e}")
finally:
    sock.close()