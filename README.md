# Coliseo OS — Sistema de Gestión de Gimnasio

Proyecto universitario para el curso **Arquitectura de Software**.  
Sistema distribuido de gestión de un gimnasio implementado con arquitectura **SOA (Service-Oriented Architecture)** usando un BUS ESB central y comunicación mediante **TCP nativo (sockets)**.

---

## Integrantes y servicios asignados

| Integrante | Servicios |
|---|---|
| Isidora | `usrol` (usuarios/roles) · `plans` (planes) |
| Benjamín | `clase` (clases) · `reser` (reservas) |
| Cristóbal | `profe` (profesores) · `notif` (notificaciones) |
| Richard | `pagos` (pagos) · `audit` (auditoría) |

---

## Arquitectura

```
┌─────────────────────────────────────────────────────┐
│                   BUS ESB (puerto 5000)              │
│              docker: jrgiadach/soabus:v1             │
└────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┘
     │      │      │      │      │      │      │
  usrol  plans  clase  reser  profe  notif  pagos  audit
```

- Todos los clientes y servicios se conectan **únicamente al BUS**, nunca entre sí directamente.
- La comunicación usa **TCP nativo** (`socket.AF_INET, socket.SOCK_STREAM`).
- Protocolo de mensajes: `[5 bytes longitud][5 chars nombre servicio][payload JSON]`

---

## Requisitos

- Python 3.8+
- Docker Desktop (para correr el BUS)

---

## Cómo ejecutar

### 1. Levantar el BUS
```bash
docker run -d -p 5000:5000 jrgiadach/soabus:v1
```

### 2. Levantar los servicios (cada uno en una terminal)
```bash
py servicios/soa_service_usrol.py
py servicios/soa_service_plans.py
py servicios/soa_service_clase.py
py servicios/soa_service_reser.py
py servicios/soa_service_profe.py
py servicios/soa_service_notif.py
py servicios/soa_service_pagos.py
py servicios/soa_service_audit.py
```

### 3. Ejecutar un cliente
```bash
py clientes/cliente_admin.py
py clientes/cliente_alumno.py
py clientes/cliente_profe.py
```

### Alternativa: script automático (Windows)
Edita `run_all.bat` reemplazando `C:\Users\Isidora\arq-sw` con la ruta de tu carpeta, luego ejecútalo.

---

## Estructura de archivos

```
arq-sw/
├── soa_lib.py                    # Librería compartida de conexión al BUS
├── run_all.bat                   # Script para levantar todo en Windows
├── servicios/
│   ├── soa_service_usrol.py
│   ├── soa_service_plans.py
│   ├── soa_service_clase.py
│   ├── soa_service_reser.py
│   ├── soa_service_profe.py
│   ├── soa_service_notif.py
│   ├── soa_service_pagos.py
│   └── soa_service_audit.py
├── clientes/
│   ├── cliente_admin.py
│   ├── cliente_alumno.py
│   └── cliente_profe.py
└── data/
    ├── usuarios.json
    ├── planes.json
    ├── clases.json
    ├── reservas.json
    ├── profesores.json
    ├── notificaciones.json
    ├── pagos.json
    └── historial.json
```

---

## Esquemas JSON por servicio

### `usrol` — Usuarios y Roles (`data/usuarios.json`)

```json
{
  "12345678-9": {
    "rut": "12345678-9",
    "nombre": "Ana Perez",
    "email": "ana@mail.com",
    "password": "1234",
    "rol": "alumno",
    "plan_activo": "plan_mensual_8",
    "clases_restantes": 7,
    "fecha_vencimiento": "2026-06-30"
  }
}
```

**Acciones:** `registrar`, `login`, `listar`, `obtener`, `actualizar_plan`

---

### `plans` — Planes (`data/planes.json`)

```json
{
  "plan_mensual_8": {
    "id": "plan_mensual_8",
    "nombre": "Mensual 8 clases",
    "precio": 35000,
    "duracion_meses": 1,
    "max_clases": 8
  }
}
```

**Acciones:** `listar_planes`, `obtener_plan`

---

### `clase` — Clases (`data/clases.json`)

```json
{
  "id_clase": "clase001",
  "disciplina": "Yoga",
  "rut_profe": "11111111-1",
  "fecha": "2026-05-24",
  "hora": "10:00",
  "cupos_max": 10,
  "cupos_disponibles": 9,
  "alumnos_inscritos": ["12345678-9"]
}
```

**Acciones:** `listar_clases`, `crear_clase`, `inscribir_alumno`, `cancelar_inscripcion`

---

### `reser` — Reservas (`data/reservas.json`)

```json
{
  "id_reserva": "reserva001",
  "rut_alumno": "12345678-9",
  "id_clase": "clase001",
  "fecha_reserva": "2026-05-24 10:00:00",
  "estado": "activa"
}
```

**Acciones:** `crear_reserva`, `cancelar_reserva`, `listar_reservas`, `reservas_por_clase`

---

### `profe` — Profesores (`data/profesores.json`)

```json
{
  "rut": "11111111-1",
  "nombre": "Profesor Juan",
  "especialidad": "Yoga"
}
```

**Acciones:** `crear_profe`, `listar_profes`, `asistencia`, `clases_profe`

---

### `notif` — Notificaciones (`data/notificaciones.json`)

```json
{
  "id": "notif_1",
  "rut_destino": "12345678-9",
  "tipo": "reserva",
  "mensaje": "Tu reserva para Yoga ha sido confirmada.",
  "fecha": "2026-05-24 10:00:00",
  "pendiente": true
}
```

**Acciones:** `enviar`, `listar_pendientes`

---

### `pagos` — Pagos (`data/pagos.json`)

```json
{
  "id_pago": "pago_20260519_152220",
  "rut_alumno": "12345678-9",
  "id_plan": "plan_mensual_8",
  "monto": 35000,
  "metodo": "efectivo",
  "estado": "aprobado",
  "fecha_pago": "2026-05-19T15:22:20.705790",
  "codigo_transaccion": "TXN20260519152220"
}
```

**Acciones:** `procesar_pago`, `listar_pagos`, `obtener_pago`

---

### `audit` — Auditoría (`data/historial.json`)

```json
{
  "id_evento": "evt_20260519_154651",
  "quien": "admin",
  "accion": "pago_registrado",
  "entidad": "12345678-9",
  "valor_anterior": "sin_pago",
  "valor_nuevo": "pago_20260519_154651",
  "fecha": "2026-05-19T15:46:51.522407"
}
```

**Acciones:** `registrar_evento`, `listar_historial`

---

## Protocolo de comunicación (soa_lib.py)

Todos los mensajes al BUS siguen el formato:

```
[00015][profe]{"accion": "listar_profes"}
  ^^^    ^^^   ^^^^^^^^^^^^^^^^^^^^^^^^
5 bytes  5 chars      JSON payload
longitud  servicio
```

Registro de servicio al iniciar:
```python
send_message(sock, "sinit", "profe")  # registra el servicio "profe"
```
