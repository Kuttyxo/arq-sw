import socket

def connect_to_bus(host='localhost', port=5000):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(f"Conectando a {host} en puerto {port}...")
    sock.connect((host, port))
    return sock

def send_message(sock, service_name, payload):
    if len(service_name) != 5:
        raise ValueError(f"El nombre del servicio debe tener 5 caracteres, recibido: '{service_name}'")
    total_length = 5 + len(payload)
    length_str = str(total_length).zfill(5)
    message = length_str.encode() + service_name.encode() + payload.encode()
    sock.sendall(message)

def receive_message(sock):
    length_data = sock.recv(5)
    if not length_data:
        return None
    total_length = int(length_data.decode())
    data = sock.recv(total_length)
    return length_data + data